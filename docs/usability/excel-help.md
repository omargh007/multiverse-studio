# Excel help sheet

Open your file from the folder on the desktop. Column **A** is `grade`, **B** is `sleep_hours`, **C** is `study_hours`. Row 1 holds the titles.

## Run a regression
1. Click the **Data** tab, then **Data Analysis** (far right).
2. Choose **Regression** and press **OK**.
3. **Input Y Range:** the `grade` column, title included (A1 down to the last row).
4. **Input X Range:**
   - to **ignore** study hours: column B only (B1 down to the last row);
   - to **keep study hours equal**: columns B and C together (B1 down to the last row of C).
5. Tick **Labels**, then press **OK**. Excel opens a new sheet with the output.
6. Find the **sleep_hours** row near the bottom:
   - **Coefficients** is the effect;
   - **P-value** is the p-value. A value such as `7.6E-06` means 0.0000076.

## Remove extreme students
1. On your data sheet, type `extreme` in cell **D1**.
2. In cell **D2** type this and press Enter:

   `=OR(ABS(A2-AVERAGE(A:A))>3*STDEV.S(A:A), ABS(B2-AVERAGE(B:B))>3*STDEV.S(B:B))`

3. Click D2 again and double-click the small square at its bottom-right corner. The formula fills down.
4. Click cell A1, then **Data > Filter**. Open the arrow on `extreme` and leave only **FALSE** ticked.
5. Select columns **A to C** by dragging across their letters, and copy (**Ctrl+C**).
6. Add a new sheet (the **+** at the bottom), click A1 and paste (**Ctrl+V**).
7. Run the regression on this new sheet. Check the last row number again: it is smaller.
