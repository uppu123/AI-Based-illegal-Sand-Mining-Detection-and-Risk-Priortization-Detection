# Export docx -> pdf (Word) and pptx -> pdf (PowerPoint), with page counts.

$dir  = "C:\Btech Project Important Files\Timeline"
$docx = Join-Path $dir "Presentation_Script_and_Reasoning.docx"
$docpdf = Join-Path $dir "Presentation_Script_and_Reasoning.pdf"
$pptx = Join-Path $dir "Project_Progress_Presentation.pptx"
$pptxpdf = Join-Path $dir "Project_Progress_Presentation.pdf"

# ---------- Word / docx
if (Test-Path $docpdf) { Remove-Item $docpdf -Force }
$w = $null
try {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false
    $w.DisplayAlerts = 0
    $d = $w.Documents.Open($docx, $false, $true)
    $d.ExportAsFixedFormat($docpdf, 17)
    "DOC PDF pages: " + $d.ComputeStatistics(2)
    $d.Close(0)
} catch {
    "DOC EXPORT FAILED: " + $_.Exception.Message
} finally {
    if ($w) { try { $w.Quit() } catch {} }
}

# ---------- PowerPoint / pptx
if (Test-Path $pptxpdf) { Remove-Item $pptxpdf -Force }
$p = $null
try {
    $p = New-Object -ComObject PowerPoint.Application
    $pres = $p.Presentations.Open($pptx, $true, $false, $false)
    "PPTX slides: " + $pres.Slides.Count
    $pres.SaveAs($pptxpdf, 32)   # 32 = ppSaveAsPDF
    $pres.Close()
    "PPTX PDF exported"
} catch {
    "PPTX EXPORT FAILED: " + $_.Exception.Message
} finally {
    if ($p) { try { $p.Quit() } catch {} }
}

# ---------- report
""
Get-ChildItem $dir -Filter "*.pdf" | Where-Object { $_.Name -match 'Presentation|Script' } |
    Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,0)}}, LastWriteTime |
    Format-Table -AutoSize
