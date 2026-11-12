Attribute VB_Name = "ScenarioSweep"
'==============================================================================
' Project 2: Forecast-to-Inventory Policy Tool
' Module: ScenarioSweep
'
' What it does
'   Runs the inventory policy model for every combination of target service
'   level and lead time (review period held fixed), records the portfolio totals from the Summary sheet,
'   and writes a trade-off table and chart to a "Scenarios" sheet.
'
' Why
'   A planner rarely asks "what is safety stock at 95%?" once. They ask
'   "what does each extra point of service cost?" and "what if the supplier
'   lead time doubles?". This macro answers both in one click.
'
' How it works
'   1. Saves the current ServiceLevel and LeadTime (named cells on Assumptions)
'   2. Loops over each scenario, writes the inputs, recalculates the workbook
'   3. Reads the named totals on Summary (Tot_SS_MA, Tot_SS_Naive, ...)
'   4. Restores the original inputs, even if an error occurs
'
' Requires named ranges created by scripts/build_workbook.py:
'   ServiceLevel, LeadTime, z, Tot_SS_Units, Tot_SS_MA, Tot_SS_Naive,
'   Tot_AvgInv, Tot_Cost
'==============================================================================
Option Explicit

Private Const OUT_SHEET As String = "Scenarios"

Public Sub RunScenarioSweep()
    Dim serviceLevels As Variant, leadTimes As Variant
    serviceLevels = Array(0.9, 0.925, 0.95, 0.975, 0.99, 0.995)
    leadTimes = Array(1, 2)

    Dim origSL As Double, origLT As Double
    Dim origCalc As XlCalculation
    Dim ws As Worksheet
    Dim i As Long, j As Long, r As Long
    Dim baseSS As Double

    If Not NamesExist() Then Exit Sub

    origSL = ThisWorkbook.Names("ServiceLevel").RefersToRange.Value
    origLT = ThisWorkbook.Names("LeadTime").RefersToRange.Value
    origCalc = Application.Calculation

    On Error GoTo CleanFail
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    Set ws = GetOrCreateSheet(OUT_SHEET)
    ws.Cells.Clear
    DeleteCharts ws
    WriteHeader ws

    r = 5
    For i = LBound(leadTimes) To UBound(leadTimes)
        For j = LBound(serviceLevels) To UBound(serviceLevels)
            ThisWorkbook.Names("LeadTime").RefersToRange.Value = leadTimes(i)
            ThisWorkbook.Names("ServiceLevel").RefersToRange.Value = serviceLevels(j)
            Application.Calculate

            ws.Cells(r, 1).Value = leadTimes(i)
            ws.Cells(r, 2).Value = serviceLevels(j)
            ws.Cells(r, 3).Value = NameValue("z")
            ws.Cells(r, 4).Value = NameValue("Tot_SS_Units")
            ws.Cells(r, 5).Value = NameValue("Tot_SS_MA")
            ws.Cells(r, 6).Value = NameValue("Tot_SS_Naive")
            ws.Cells(r, 7).Value = ws.Cells(r, 6).Value - ws.Cells(r, 5).Value
            ws.Cells(r, 8).Value = NameValue("Tot_AvgInv")
            ws.Cells(r, 9).Value = NameValue("Tot_Cost")
            r = r + 1
        Next j
    Next i

    ' Extra safety stock $ vs the 95%, 1-week base case (row with L=1, CSL=95%)
    baseSS = BaseCaseSS(ws, 5, r - 1)
    For i = 5 To r - 1
        If baseSS > 0 Then ws.Cells(i, 10).Value = ws.Cells(i, 5).Value / baseSS - 1
    Next i

    FormatTable ws, r - 1
    AddChart ws, 5, r - 1, UBound(serviceLevels) - LBound(serviceLevels) + 1

CleanExit:
    ThisWorkbook.Names("ServiceLevel").RefersToRange.Value = origSL
    ThisWorkbook.Names("LeadTime").RefersToRange.Value = origLT
    Application.Calculation = origCalc
    Application.Calculate
    Application.ScreenUpdating = True
    If Err.Number = 0 Then
        ws.Activate
        MsgBox "Scenario sweep finished: " & (r - 5) & " scenarios." & vbNewLine & _
               "Assumptions restored to service level " & Format(origSL, "0.0%") & _
               " and lead time " & origLT & " week(s).", vbInformation
    End If
    Exit Sub

CleanFail:
    MsgBox "Scenario sweep stopped: " & Err.Description & vbNewLine & _
           "Assumptions have been restored.", vbExclamation
    Resume CleanExit
End Sub

'--- helpers -----------------------------------------------------------------

Private Function NamesExist() As Boolean
    Dim req As Variant, k As Long, nm As Name
    req = Array("ServiceLevel", "LeadTime", "z", "Tot_SS_Units", "Tot_SS_MA", _
                "Tot_SS_Naive", "Tot_AvgInv", "Tot_Cost")
    For k = LBound(req) To UBound(req)
        Set nm = Nothing
        On Error Resume Next
        Set nm = ThisWorkbook.Names(req(k))
        On Error GoTo 0
        If nm Is Nothing Then
            MsgBox "Missing named range: " & req(k) & vbNewLine & _
                   "Rebuild the workbook with scripts/build_workbook.py.", vbCritical
            NamesExist = False
            Exit Function
        End If
    Next k
    NamesExist = True
End Function

Private Function NameValue(nm As String) As Double
    NameValue = ThisWorkbook.Names(nm).RefersToRange.Value
End Function

Private Function GetOrCreateSheet(sheetName As String) As Worksheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(sheetName)
    On Error GoTo 0
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
        ws.Name = sheetName
    End If
    Set GetOrCreateSheet = ws
End Function

Private Sub DeleteCharts(ws As Worksheet)
    Do While ws.ChartObjects.Count > 0
        ws.ChartObjects(1).Delete
    Loop
End Sub

Private Sub WriteHeader(ws As Worksheet)
    ws.Range("A1").Value = "Scenario sweep: service level x lead time"
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 14
    ws.Range("A2").Value = "Generated by macro RunScenarioSweep on " & Format(Now, "yyyy-mm-dd hh:nn") & _
        ". Other assumptions (including review period) held at their Assumptions sheet values. Values, not formulas: re-run after changing assumptions."
    ws.Range("A2").Font.Italic = True
    ws.Range("A4:J4").Value = Array("Lead time (wk)", "Service level", "z", _
        "Safety stock (units)", "Safety stock $ (moving avg)", "Safety stock $ (naive)", _
        "SS $ saved by moving avg", "Avg inventory $", "Total annual cost $", _
        "SS $ vs base case (1 wk, 95%)")
    With ws.Range("A4:J4")
        .Font.Bold = True
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = RGB(31, 78, 121)
        .WrapText = True
        .VerticalAlignment = xlCenter
        .HorizontalAlignment = xlCenter
    End With
    ws.Rows(4).RowHeight = 32
End Sub

Private Function BaseCaseSS(ws As Worksheet, firstRow As Long, lastRow As Long) As Double
    Dim i As Long
    For i = firstRow To lastRow
        If ws.Cells(i, 1).Value = 1 And Abs(ws.Cells(i, 2).Value - 0.95) < 0.0001 Then
            BaseCaseSS = ws.Cells(i, 5).Value
            Exit Function
        End If
    Next i
    BaseCaseSS = 0
End Function

Private Sub FormatTable(ws As Worksheet, lastRow As Long)
    ws.Range("A5:A" & lastRow).NumberFormat = "0"
    ws.Range("B5:B" & lastRow).NumberFormat = "0.0%"
    ws.Range("C5:C" & lastRow).NumberFormat = "0.000"
    ws.Range("D5:D" & lastRow).NumberFormat = "#,##0"
    ws.Range("E5:I" & lastRow).NumberFormat = "$#,##0"
    ws.Range("J5:J" & lastRow).NumberFormat = "+0.0%;-0.0%;0.0%"
    ws.Range("A4:J" & lastRow).Borders.Color = RGB(191, 191, 191)
    ws.Range("A4:J" & lastRow).Font.Name = "Arial"
    ws.Columns("A:J").ColumnWidth = 15
End Sub

Private Sub AddChart(ws As Worksheet, firstRow As Long, lastRow As Long, nPerLT As Long)
    ' One line per lead time: safety stock $ (moving avg) against service level
    Dim co As ChartObject, s As Series
    Dim startRow As Long, k As Long, nSeries As Long

    Set co = ws.ChartObjects.Add(Left:=ws.Range("L4").Left, Top:=ws.Range("L4").Top, _
                                 Width:=480, Height:=290)
    With co.Chart
        .ChartType = xlLineMarkers
        Do While .SeriesCollection.Count > 0
            .SeriesCollection(1).Delete
        Loop
        nSeries = (lastRow - firstRow + 1) \ nPerLT
        For k = 0 To nSeries - 1
            startRow = firstRow + k * nPerLT
            Set s = .SeriesCollection.NewSeries
            s.Name = "Lead time " & ws.Cells(startRow, 1).Value & " wk"
            s.XValues = ws.Range(ws.Cells(startRow, 2), ws.Cells(startRow + nPerLT - 1, 2))
            s.Values = ws.Range(ws.Cells(startRow, 5), ws.Cells(startRow + nPerLT - 1, 5))
        Next k
        .HasTitle = True
        .ChartTitle.Text = "Safety stock $ rises steeply as service level approaches 100%"
        .Axes(xlCategory).HasTitle = True
        .Axes(xlCategory).AxisTitle.Text = "Target cycle service level"
        .Axes(xlValue).HasTitle = True
        .Axes(xlValue).AxisTitle.Text = "Safety stock $ (moving avg forecast)"
        .Axes(xlValue).TickLabels.NumberFormat = "$#,##0"
        .HasLegend = True
        .Legend.Position = xlLegendPositionBottom
    End With
End Sub
