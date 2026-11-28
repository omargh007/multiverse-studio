# Task sheet

Participant code: ______   Tool: App / Excel   File: study_a.csv / study_b.csv

## The question
A school asks: **do students who sleep more get higher grades?**

The file has one row per student:
- `grade`: course grade, 0 to 100
- `sleep_hours`: hours of sleep per night
- `study_hours`: hours of study per day

Treat study hours as **fair to keep equal**: students decide how much they study before they get a grade, and neither the grade nor sleep is what causes it.

## Four ways to analyse it
Each way is a **linear regression** that predicts `grade` from `sleep_hours`. It gives the **effect**: how many grade points go with one extra hour of sleep.

| Way | Extreme values | Study hours |
|---|---|---|
| 1 | Keep every student | Ignore them |
| 2 | Keep every student | Keep them equal (compare students who study the same amount) |
| 3 | Remove extreme students | Ignore them |
| 4 | Remove extreme students | Keep them equal |

- **Extreme student:** their grade or their sleep hours is more than **3 standard deviations** from the average.
- A result is **clear** when its **p-value is below 0.05**.
- Use only these two choices. Don't add any others.

## Your answers
**Q1.** Way 1: effect of one extra hour of sleep, in grade points (2 decimals): ________

**Q2.** Way 2: effect (2 decimals): ________

**Q3.** In how many of the four ways is the result clear?   0   1   2   3   4

**Q4.** Which choice changes **whether the result is clear**?

&nbsp;&nbsp;&nbsp;&nbsp;Extreme values   /   Study hours   /   Neither

**Q5.** In one sentence, what would you tell the school?

____________________________________________________________

When you have finished, say **done**.
