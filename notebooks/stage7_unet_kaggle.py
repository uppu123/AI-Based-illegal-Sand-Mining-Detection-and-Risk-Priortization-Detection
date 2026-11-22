# %% [markdown]
# # Stage 7 - U-Net Segmentation (Kaggle)
# 
# **Protocol (must follow)**
# - Uses human pixel masks only (`annotation/masks/*_mask.png` + `annotation/chips.json`).
# - **2024 excluded from model selection/early stopping**. 2024 mask chips are held out from CV/selection and reported separately.
# - **No augmentation before split / no test leakage**. Augmentation (flip/90° rotation) applied only to training fold samples.
# - **GroupKFold by transect** for CV on 2023 mask chips.
# - Sequential single-run (no parallel training jobs).
# - Metrics are honest; sparse/tiny masks can yield near-zero IoU/Dice - report as-is.

# %%
import json, os, random, platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import rasterio
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import GroupKFold
from torch.utils.data import DataLoader, TensorDataset

# %% [markdown]
# ## Config

# %%
INPUT_DIR = Path(os.environ.get("YAMUNA_STAGE7_INPUT", "/kaggle/input/yamuna-stage7"))
CHIPS_DIR = Path(os.environ.get("YAMUNA_STAGE7_CHIPS", str(INPUT_DIR / "chips_fixed")))
MASKS_DIR = Path(os.environ.get("YAMUNA_STAGE7_MASKS", str(INPUT_DIR / "annotation" / "masks")))
CHIPS_JSON = Path(os.environ.get("YAMUNA_STAGE7_CHIPS_JSON", str(INPUT_DIR / "annotation" / "chips.json")))
OUTPUT_DIR = Path(os.environ.get("YAMUNA_STAGE7_OUTPUT", "/kaggle/working/stage7_unet"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARCH = "unet"  # Stage 7 U-Net only; LMS-Net blocked unless on-disk arch ref
BASE = 16
EPOCHS = int(os.environ.get("STAGE7_EPOCHS", "40"))
BATCH_SIZE = 4
LR = 1e-3
SEED = 42
CV_SPLITS = 3
THRESH = 0.5
EXCLUDE_2024_FROM_SELECTION = True

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device", device)

# %% [markdown]
# ## Model

# %%
class UNet(nn.Module):
    def __init__(self, in_ch=14, base=16):
        super().__init__()
        def block(i,o):
            return nn.Sequential(
                nn.Conv2d(i,o,3,padding=1,bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
                nn.Conv2d(o,o,3,padding=1,bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True))
        self.e1,self.e2,self.e3,self.e4 = block(in_ch,base), block(base,base*2), block(base*2,base*4), block(base*4,base*8)
        self.bottleneck = block(base*8, base*16)
        self.pool = nn.MaxPool2d(2)
        def up(i,o):
            return nn.Sequential(
                nn.Conv2d(i,o,3,padding=1,bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
                nn.Conv2d(o,o,3,padding=1,bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True))
        self.d4=up(base*16+base*8,base*8); self.d3=up(base*8+base*4,base*4)
        self.d2=up(base*4+base*2,base*2); self.d1=up(base*2+base,base)
        self.out=nn.Conv2d(base,1,1)
    def forward(self,x):
        e1=self.e1(x); e2=self.e2(self.pool(e1)); e3=self.e3(self.pool(e2)); e4=self.e4(self.pool(e3))
        z=self.bottleneck(self.pool(e4))
        for up,e in [(self.d4,e4),(self.d3,e3),(self.d2,e2),(self.d1,e1)]:
            z=up(torch.cat([F.interpolate(z,size=e.shape[2:],mode='bilinear',align_corners=False),e],dim=1))
        return self.out(z)

def bce_dice(logits, target):
    bce = F.binary_cross_entropy_with_logits(logits, target)
    prob = torch.sigmoid(logits)
    inter = (prob*target).sum(dim=(2,3))
    dice = (2*inter+1)/(prob.sum(dim=(2,3))+target.sum(dim=(2,3))+1)
    return bce + (1-dice).mean()

# %% [markdown]
# ## Data

# %%
entries = json.loads(CHIPS_JSON.read_text(encoding="utf-8"))
print("mask entries", len(entries))

def load_chip(e):
    p = CHIPS_DIR / e["quarter"] / f"{e['chip_id']}.tif"
    with rasterio.open(p) as ds:
        arr = ds.read().astype(np.float32)
    arr[:10] /= 10000.0
    arr[10:] = arr[10:] / 5000.0 - 1.0
    return arr

def load_mask(e):
    p = MASKS_DIR / f"{e['chip_id']}_mask.png"
    with Image.open(p) as im:
        m = np.asarray(im.convert("L"), dtype=np.float32)
    if m.shape != (256,256):
        m = np.asarray(Image.fromarray(m.astype(np.uint8)).resize((256,256)), dtype=np.float32)
    return (m > 127).astype(np.float32)

def augment(x,y):
    out=[]
    for k in range(4):
        xr,yr=np.rot90(x,k,axes=(1,2)), np.rot90(y,k)
        out.append((xr.copy(), yr.copy()))
        out.append((np.flip(xr,axis=2).copy(), np.flip(yr,axis=1).copy()))
    return out

def compute_metrics(y_true, y_prob, threshold=THRESH):
    pred = y_prob >= threshold
    truth = y_true.astype(bool)
    tp=int((pred&truth).sum()); fp=int((pred&~truth).sum()); fn=int((~pred&truth).sum()); tn=int((~pred&~truth).sum())
    prec = tp/(tp+fp) if tp+fp else 0.0
    rec = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*prec*rec/(prec+rec) if prec+rec else 0.0
    iou = tp/(tp+fp+fn) if tp+fp+fn else 0.0
    dice = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=prec,recall=rec,f1=f1,iou=iou,dice=dice,positive_fraction=float(truth.mean()))

# split: 2023 for CV/selection, 2024 held out from selection
cv_entries = [e for e in entries if not str(e["quarter"]).startswith("2024")]
heldout_2024 = [e for e in entries if str(e["quarter"]).startswith("2024")]
print("cv_entries(2023)", len(cv_entries), "heldout_2024", len(heldout_2024))

# preload
cache={}
for e in entries:
    cache[e["chip_id"]] = (load_chip(e), load_mask(e))

# %% [markdown]
# ## CV on 2023 mask chips

# %%
X,Y,G,CHIP=[],[],[],[]
for e in cv_entries:
    x,y = cache[e["chip_id"]]
    for xa,ya in augment(x,y):
        X.append(xa); Y.append(ya); G.append(e["transect_id"]); CHIP.append(e["chip_id"])
X=np.stack(X); Y=np.stack(Y)[:,None]; G=np.asarray(G)
print("cv dataset", X.shape, "groups", len(set(G)))

fold_reports=[]
for fold,(tr,va) in enumerate(GroupKFold(n_splits=CV_SPLITS).split(X,Y,G),1):
    mean=X[tr].mean(axis=(0,2,3),keepdims=True); std=X[tr].std(axis=(0,2,3),keepdims=True)+1e-6
    xtr=torch.from_numpy(((X[tr]-mean)/std).astype(np.float32)); ytr=torch.from_numpy(Y[tr].astype(np.float32))
    xva=torch.from_numpy(((X[va]-mean)/std).astype(np.float32))
    loader=DataLoader(TensorDataset(xtr,ytr), batch_size=BATCH_SIZE, shuffle=True)
    model=UNet(base=BASE).to(device); opt=torch.optim.Adam(model.parameters(), lr=LR)
    best_iou,best_state,best_epoch=-1,None,-1
    for epoch in range(1,EPOCHS+1):
        model.train(); loss_sum=0.0
        for xb,yb in loader:
            xb,yb=xb.to(device),yb.to(device)
            opt.zero_grad(); loss=bce_dice(model(xb),yb); loss.backward(); opt.step(); loss_sum+=loss.item()*len(xb)
        model.eval()
        with torch.no_grad(): p=torch.sigmoid(model(xva.to(device))).cpu().numpy()
        m=compute_metrics(Y[va][:,0], p)
        if m["iou"]>best_iou:
            best_iou, best_epoch = m["iou"], epoch
            best_state={k:v.cpu().clone() for k,v in model.state_dict().items()}
        if epoch%10==0 or epoch==1:
            print(f"fold {fold} epoch {epoch:2d} loss {loss_sum/len(xtr):.4f} val_iou {m['iou']:.4f}")
    model.load_state_dict(best_state); model.eval()
    with torch.no_grad(): prob=torch.sigmoid(model(xva.to(device))).cpu().numpy()
    m=compute_metrics(Y[va][:,0], prob); m.update(fold=fold,best_epoch=best_epoch,val_chips=sorted(set(np.asarray(CHIP)[va].tolist())))
    fold_reports.append(m)
    torch.save(dict(state=best_state,arch=ARCH,base=BASE,mean=mean,std=std,best_epoch=best_epoch), OUTPUT_DIR/f"fold_{fold}.pt")
    print("fold", fold, "iou", m["iou"], "dice", m["dice"])

# %% [markdown]
# ## Final fit on all 2023 mask chips, evaluate on held-out 2024 masks (report only)

# %%
Xall,Yall=[],[]
for e in cv_entries:
    x,y=cache[e["chip_id"]]
    for xa,ya in augment(x,y): Xall.append(xa); Yall.append(ya)
Xall=np.stack(Xall); Yall=np.stack(Yall)[:,None]
mean=Xall.mean(axis=(0,2,3),keepdims=True); std=Xall.std(axis=(0,2,3),keepdims=True)+1e-6
xtr=torch.from_numpy(((Xall-mean)/std).astype(np.float32)); ytr=torch.from_numpy(Yall.astype(np.float32))
loader=DataLoader(TensorDataset(xtr,ytr), batch_size=BATCH_SIZE, shuffle=True)
model=UNet(base=BASE).to(device); opt=torch.optim.Adam(model.parameters(), lr=LR)
for epoch in range(1,EPOCHS+1):
    model.train(); loss_sum=0.0
    for xb,yb in loader:
        xb,yb=xb.to(device),yb.to(device)
        opt.zero_grad(); loss=bce_dice(model(xb),yb); loss.backward(); opt.step(); loss_sum+=loss.item()*len(xb)
    if epoch%10==0 or epoch==1:
        print(f"final epoch {epoch:2d} loss {loss_sum/len(xtr):.4f}")
model.eval()
torch.save(dict(state={k:v.cpu().clone() for k,v in model.state_dict().items()},arch=ARCH,base=BASE,mean=mean,std=std), OUTPUT_DIR/"final_2023.pt")

heldout_rows=[]
for e in heldout_2024:
    x,y=cache[e["chip_id"]]
    xin=torch.from_numpy(((x-mean.squeeze(0))/std.squeeze(0)).astype(np.float32)[None]).to(device)
    with torch.no_grad(): prob=torch.sigmoid(model(xin)).cpu().numpy()[0,0]
    m=compute_metrics(y, prob); m.update(chip_id=e["chip_id"], quarter=e["quarter"], transect_id=e["transect_id"]); heldout_rows.append(m)
heldout_df=pd.DataFrame(heldout_rows)
if len(heldout_df):
    heldout_df.to_csv(OUTPUT_DIR/"heldout_2024_predictions.csv", index=False)
    heldout_summary={k:float(heldout_df[k].mean()) for k in ["iou","dice","precision","recall","f1"]}
else:
    heldout_summary={}

# %% [markdown]
# ## Save metrics

# %%
overall={k:float(np.mean([f[k] for f in fold_reports])) for k in ["iou","dice","precision","recall","f1"]}
metrics={
    "stage":7,"model":"UNet","arch":ARCH,"base":BASE,"epochs":EPOCHS,"seed":SEED,"device":str(device),
    "timestamp_utc":datetime.now(timezone.utc).isoformat(),
    "n_mask_entries_total":len(entries),
    "n_cv_2023":len(cv_entries),"n_heldout_2024":len(heldout_2024),
    "cv_overall":overall,"cv_folds":fold_reports,
    "heldout_2024_summary_report_only":heldout_summary,
    "protocol_notes":[
        "2024 excluded from CV/model selection/early stopping; held out for report only.",
        "Augmentation (flip/90deg) applied only to training fold samples.",
        "GroupKFold by transect on 2023 mask chips.",
        "No test leakage; held-out 2024 not used for selection.",
        "Sparse/tiny masks may produce near-zero IoU/Dice; report as-is."
    ]
}
(OUTPUT_DIR/"metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
pd.DataFrame(fold_reports).to_csv(OUTPUT_DIR/"cv_fold_metrics.csv", index=False)
print(json.dumps({"cv_overall":overall, "heldout_2024_summary":heldout_summary}, indent=2))
