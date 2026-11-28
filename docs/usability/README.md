# Usability study

Can people outside computer science check a finding faster and more correctly with Multiverse Studio than with Excel, and how usable do they find each?

## Files
| File | Print? | What it is |
|---|---|---|
| `consent.md` | 1 per person | Information and signature. Fill in the names first. |
| `task-sheet.md` | 2 per person | The same questions for both tools. |
| `excel-help.md` | 1, reusable | Given **only** during the Excel task. |
| `questionnaire.md` | 1 per person | Background questions, then SUS once per tool. |
| `data/study_a.csv`, `data/study_b.csv` | no | The two datasets. Simulated, safe to share. |
| `data/answer_key.json` | **never show** | Correct answers. |
| `results.csv` | no | You type one row per participant. |
| `score.py` | no | Turns `results.csv` into `summary.md`. |
| `make_data.py` | no | Rebuilds the datasets and the answer key. |

## Design
- **Participants:** 8 recommended (minimum 5, maximum 10). Adults whose studies or job are not computer science or data science. Anyone who has used Multiverse Studio before, or helped build it, is excluded. Give out codes at random: shuffle the booked people before numbering them.
- **Within subjects:** every person does the task in both tools, once on set A and once on set B.
- **Place:** in person, one laptop, same screen and mouse for everyone.
- **Task:** four analyses of "do students who sleep more get higher grades?" (see the task sheet).
- **Measures:** time on task, correct answers (Q1 to Q4), completion within 15 minutes, SUS score for each tool.
- **Help:** Excel users get a written help sheet. App users get none. This favours Excel on purpose, so a speed or accuracy advantage for the app cannot come from better instructions.
- **Choosing options in the app is part of the task.** The app also suggests a third extreme-value rule (1.5 IQR), which the participant has to untick. Record how many analyses they ran.

### Order (counterbalancing)
Repeat this block. Eight participants give each row twice.

| Participant | First task | Second task |
|---|---|---|
| P01, P05, P09 | App, set A | Excel, set B |
| P02, P06, P10 | Excel, set A | App, set B |
| P03, P07 | App, set B | Excel, set A |
| P04, P08 | Excel, set B | App, set A |

## Before the first session
1. Turn on Excel's regression tool once: **File > Options > Add-ins**, choose *Excel Add-ins* next to **Manage**, press **Go**, tick **Analysis ToolPak**. A **Data Analysis** button appears on the **Data** tab.
2. Check the app starts: `python -m multiverse_studio`.
3. Do one full practice run yourself with each tool. Don't record it.
4. **Do not start without an answer:** ask the instructor whether your university requires ethics approval or an exemption. A journal such as SoftwareX can ask for that statement. Write the answer here: __________
5. Fill in the names, email and withdrawal date in `consent.md` and print the sheets.

## Before each participant (3 minutes)
1. Make a new folder on the desktop named with the code (`P01`) and copy fresh `study_a.csv` and `study_b.csv` into it. Do not copy the answer key.
2. Close Excel. Don't save changes from the last person.
3. In the app's browser tab, press refresh. The welcome screen should appear with no data loaded.
4. Set the browser and Excel to 100% zoom.

## Session script (about 45 minutes)
Read the quoted lines aloud, the same way every time.

1. **Welcome and consent** (3 min). "We are testing two tools, not you. You can stop at any time." Don't say which tool the team made. Collect the signature.
2. **Background questions** (2 min).
3. **First task** (15 min at most).
   - App: the browser shows the welcome screen. Excel: Excel is closed.
   - Give the task sheet face down. "The file is in the folder on the desktop. Use only this tool. Say *done* when you have written your answers. I can't help during the task."
   - "Start." Turn the sheet over and start the timer.
   - Stop the timer at *done*. At 15:00, stop them, record 900 seconds and *completed = no*, and keep whatever they wrote.
4. **SUS for that tool** (2 min).
5. **Second task** with the other tool and the other dataset (15 min at most).
6. **SUS for the second tool** (2 min).
7. **Short talk** (3 min). "What was hardest? What would you change? Which would you use again, and why?" Write the answers as notes.
8. **Debrief** (1 min). Say that your team built Multiverse Studio, and that honest criticism of it is welcome.

If someone asks for help, say only: "Do what you would do if I weren't here." If the app or laptop crashes, note it, restart that task and mark it in the notes.

## Recording
Type one row per participant into `results.csv` on the same day.

| Column | Value |
|---|---|
| `participant` | code only, `P01` |
| `first_tool` | `app` or `excel` |
| `app_set`, `excel_set` | `A` or `B` |
| `background` | the area they ticked, nothing more detailed |
| `excel_experience` | `never`, `basic` or `regression` |
| `statistics_course` | `yes` or `no` |
| `app_analyses` | how many analyses the app ran (4 if they unticked the extra rule); blank if they never ran it |
| `app_q5`, `excel_q5` | their sentence, to read and quote; it is not scored |
| `app_seconds`, `excel_seconds` | whole seconds, `900` if time ran out |
| `app_completed`, `excel_completed` | `yes` if they said *done* in time, otherwise `no` |
| `app_q1` to `app_q4`, `excel_q1` to `excel_q4` | what they wrote; leave blank if empty. Q4 is `extreme values`, `study hours` or `neither` |
| `sus_app_1` to `sus_app_10`, `sus_excel_1` to `sus_excel_10` | 1 to 5 |
| `notes` | comments, crashes, anything unusual. No names or details that identify someone |

Then run:

```bash
python docs/usability/score.py
```

It checks the rows and writes `summary.md`. Q1 and Q2 count as correct within 0.01 of the key. Q3 and Q4 must match it exactly.

## How the datasets were chosen
`make_data.py` takes the first simulator seed, counting from 1, where the app offers exactly the task's two choices, removing extreme values drops at least one student, and every p-value is below 0.001 or above 0.5 in the pattern the scenario implies. The rule looks only at the data, never at the app's verdict. It favours clear-cut cases, so report it.

## Reporting
- Report the number of people, medians and ranges, completion and correct-answer counts, and mean SUS for each tool.
- With 5 to 10 people these are descriptions. Don't report significance tests or claim the result holds for everyone. Show each person's times as well as the medians.
- Report the dataset and first-task rows from `summary.md`. The two sets are not identical in difficulty, and knowledge from the first task carries into the second.
- Times that hit the 15-minute limit are really "longer than 15 minutes". Say how many there were.
- Report problems people had with the app as plainly as the successes.
- State these limits: the session leader is one of the developers; the task is exactly the kind of job the app was built for; Excel users had a help sheet and app users did not; the data are simulated and clear-cut.
- SUS is from Brooke, J. (1996). *SUS: A "quick and dirty" usability scale.* In Usability Evaluation in Industry. Taylor & Francis.

## Privacy
This repository is public. Never commit names, signed consent forms, contact details or anything that identifies a participant. Use codes only, and keep the signed forms on paper. After the withdrawal date, black out the participant code on each signed form, so names can no longer be linked to results.

## Invitation message
> Hello! We are three students studying how people check research findings with software, and we need people who do **not** study computer science or data science. It takes about 45 minutes, in person. You answer a few questions about a small made-up dataset using two different tools. No preparation or statistics knowledge is needed. We record your times and answers under a code, not your name. Would you like to take part? Reply with a time that suits you.
