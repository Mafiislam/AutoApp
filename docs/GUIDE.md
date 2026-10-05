# AutoApp beginner guide

The guide takes you from nothing to your first finished job application package. You do not need to know how to code. Follow the steps in order. Each step says what to type and what you should see.

## Contents

1. What AutoApp does, and what it does not do
2. What you need before you start
3. Install AutoApp
4. Get your keys
5. Set up your profile
6. Find jobs
7. Make your first application package
8. Check and finish your package
9. Jobs from LinkedIn, Indeed and StepStone
10. Daily routine
11. Settings you can change
12. Costs and privacy
13. Fixing common problems
14. Updating AutoApp
15. Words explained

---

## 1. What AutoApp does, and what it does not do

AutoApp helps you apply for jobs faster. For each job it:

1. Researches the company.
2. Compares the job advert with your skills, experience, education and interests.
3. Writes a CV and a cover letter for that job, in plain and natural language.
4. Saves everything in a folder on your computer.

AutoApp does **not** send applications. You read each document, change what you want, and send it yourself. That is on purpose. Employers notice generic applications, and you are the only person who can check that every fact is true.

AutoApp also does not log in to LinkedIn, Indeed or StepStone. Their rules do not allow automated searching. Section 9 shows how to use those sites with AutoApp in a safe way.

## 2. What you need before you start

| You need | Where to get it | Cost |
|---|---|---|
| A Mac, Windows or Linux computer | You have it | Free |
| Python 3.10 or newer | python.org/downloads | Free |
| Git | git-scm.com/downloads | Free |
| An Anthropic API key | console.anthropic.com | Pay as you go |
| An Adzuna key (recommended) | developer.adzuna.com | Free |

To check Python, open a terminal and type:

```bash
python3 --version
```

On Windows, type `py --version` instead. You should see a number such as `Python 3.12.1`. If the number starts with 3.10 or higher, you are fine.

**How to open a terminal**

- **Mac:** press Command and Space, type `Terminal`, press Enter.
- **Windows:** press the Windows key, type `PowerShell`, press Enter.

## 3. Install AutoApp

Type these commands one block at a time. Wait for each block to finish before you type the next.

**Step 1. Download the project**

```bash
cd ~
git clone https://github.com/Mafiislam/AutoApp.git
cd AutoApp
```

On Windows, use `cd $HOME` instead of `cd ~`.

**Step 2. Create a private Python environment**

An environment keeps AutoApp separate from other things on your computer.

Mac and Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If Windows says scripts are disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, and try again.

After this, your prompt starts with `(.venv)`. That means the environment is on.

**Step 3. Install**

```bash
pip install -e .
```

**Step 4. Test**

```bash
autoapp --help
```

You should see a list of commands such as `init`, `search`, `run` and `apply-url`. If you see "command not found", read Section 13.

> **Important:** every time you open a new terminal, go to the project folder and switch the environment on again:
> ```bash
> cd ~/AutoApp
> source .venv/bin/activate
> ```
> On Windows the second line is `.venv\Scripts\Activate.ps1`.

## 4. Get your keys

A key is a long password that lets AutoApp use a service. Keep keys private. Never post them online or send them to other people.

### 4.1 Anthropic key (needed for writing and research)

1. Go to console.anthropic.com and create an account.
2. Add a small amount of credit under Billing. Five dollars is plenty to start.
3. Open API Keys and create a new key. Copy it. It starts with `sk-ant-`.

### 4.2 Adzuna keys (recommended for job search)

1. Go to developer.adzuna.com and register for free.
2. On your dashboard you will see an **App ID** (numbers) and an **App Key** (letters and numbers).

Without Adzuna, AutoApp can still search one smaller job board, but you will find far fewer jobs.

### 4.3 Tell AutoApp your keys

Type each line below **on one line**, with your real value right after the `=` sign. No spaces. No line break.

Mac and Linux:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export ADZUNA_APP_ID=your-app-id
export ADZUNA_APP_KEY=your-app-key
```

Windows PowerShell:
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
$env:ADZUNA_APP_ID="your-app-id"
$env:ADZUNA_APP_KEY="your-app-key"
```

Check that a key is set (Mac and Linux):
```bash
echo $ADZUNA_APP_ID
```
It should print your App ID.

Your keys last only until you close the terminal. To keep them:

- **Mac:** type `open -e ~/.zshrc`, paste the three `export` lines at the end, save, then run `source ~/.zshrc`.
- **Windows:** use `setx ANTHROPIC_API_KEY "sk-ant-your-key-here"` for each key, then open a new PowerShell window.

## 5. Set up your profile

Your profile is the most important part. AutoApp may only use facts that are in your profile. A short or vague profile gives weak CVs. A full and true profile gives strong ones.

### 5.1 Create the files

Make sure you are in the project folder, then run:

```bash
autoapp init
```

The command creates two files in the folder: `profile.yaml` (about you) and `config.yaml` (program settings).

### 5.2 Open your profile

- **Mac:** `open -e profile.yaml`
- **Windows:** `notepad profile.yaml`

Use a plain text editor like these. Do not use Word.

### 5.3 Fill it in

The file is in a format called YAML. Three rules keep it working:

- Spacing matters. Keep the indents (the spaces at the start of lines) exactly as in the example.
- Keep the colon after each name, such as `title:`.
- Put text in quotes if it contains a colon, for example `"Project: climate policy"`.

Here is what each part means.

```yaml
name: Your Full Name
email: you@example.com
phone: "+49 000 000000"
location: Berlin, Germany
links:
  - linkedin.com/in/yourname
headline: PhD researcher in political science and AI governance
summary: >
  Two or three plain sentences about who you are professionally.
```

**skills** are the tools and methods you really have. AutoApp matches them against adverts, and it never adds a skill that is not on your list.

```yaml
skills:
  - Python
  - Survey research
  - Policy analysis
  - Academic writing
```

**experience** lists your jobs, newest first. Write bullets that say what you did, with numbers when you have them.

```yaml
experience:
  - title: Doctoral Researcher
    company: Example University
    location: Berlin
    start: "2022"
    end: present
    bullets:
      - Built a text analysis pipeline for 40,000 parliamentary speeches in Python
      - Taught a seminar on AI and public policy to 30 master students
```

**education**, **languages** and **interests** work the same way. Interests are used when scoring jobs, so list the topics you really want to work on.

**extra_sections** holds anything else, such as publications or projects. It is copied to the CV as written.

### 5.4 The search block

The search block tells AutoApp which jobs to look for.

```yaml
search:
  keywords:
    - "AI governance"
    - "policy advisor"
    - "research associate"
    - "wissenschaftlicher Mitarbeiter"
  locations: ["Berlin", "Hamburg", "Munich"]
  countries: ["de"]
  max_age_days: 14
  remote_ok: true
  min_score: 25
  exclude_keywords: ["intern", "praktikum", "sales"]
```

| Setting | Meaning |
|---|---|
| `keywords` | Job titles or topics to search for. Use English and German words if you apply in Germany. |
| `locations` | Cities to search in. Leave the list empty to search everywhere. |
| `countries` | Country codes for Adzuna: `de` Germany, `gb` UK, `us` USA, `nl` Netherlands, `at` Austria, `fr` France |
| `max_age_days` | Only jobs posted within this many days are shown. |
| `remote_ok` | `true` gives remote jobs a better score. |
| `min_score` | Jobs below this score from 0 to 100 are hidden. 25 to 40 works well. |
| `exclude_keywords` | Jobs with these words in the title are dropped. |

Save the file when you are done.

## 6. Find jobs

```bash
autoapp search
```

The search is free. It does not use the Anthropic key. You will see a list like this:

```
Found 87 jobs, 87 not seen before, 12 with score >= 25.

 41.5  Policy Advisor AI Regulation | Example GmbH | Berlin | https://...
 38.0  Research Associate Digital Governance | Institute X | Hamburg | https://...
```

The number on the left is the match score from 0 to 100. It is calculated from your skills, the job title, your interests, the location and how recent the job is. Links open the advert.

**If the list is empty**, the message above the list tells you why:

- "Found 0 jobs": your keywords or locations are too narrow. Add keywords, raise `max_age_days`, or empty `locations`.
- "Found 87 jobs, 0 with score": lower `min_score`, or try once with `autoapp search --min-score 10`.

Change `profile.yaml`, save, and run the search again until the top results look like jobs you would want.

## 7. Make your first application package

Start with one job, so you can check the quality and the cost:

```bash
autoapp run --limit 1
```

The run takes one to three minutes. You will see steps appear: researching the company, comparing the advert and your profile, tailoring the CV, writing the cover letter, and the folder where it saved the result.

AutoApp may skip a job when the fit is poor and tell you why. To make a package anyway, use `apply-url` or `apply-file` with `--force` (Section 9).

To make packages for more jobs at once:

```bash
autoapp run --limit 5
```

Jobs you have already processed are not repeated. To see the history:

```bash
autoapp list
```

## 8. Check and finish your package

Open the `applications` folder. Each job has its own folder, named with the date, the company and the role.

| File | What it is |
|---|---|
| `README.md` | Your checklist, and any problems the writing checker found. Start here. |
| `fit_analysis.md` | Match score, your strongest points, and the gaps. |
| `company_research.md` | What the company does, its culture, news, and details you could mention. |
| `CV_<name>.docx` | Your tailored CV. |
| `CoverLetter_<name>.docx` | Your cover letter. |
| `CoverLetter.txt` | The same letter as plain text, for online forms. |
| `job_description.txt` | The advert as AutoApp read it. |

### The review routine

Do these checks every time. They take about ten minutes and protect you.

1. **Facts.** Compare every date, job title, employer and number in the CV with your real record. AutoApp copies titles, employers and dates from your profile, but check anyway.
2. **Claims about the company.** Read `company_research.md`. If the letter mentions a project or news item, open the source and confirm it is real and current.
3. **Voice.** Read the cover letter out loud. Change any sentence you would not say. Add one detail that only you would know.
4. **Gaps.** Read the gaps in `fit_analysis.md`. Decide if you want to mention how you would close them.
5. **Format.** If the employer wants a PDF, open the Word file and choose File, then Save as PDF.
6. **Names.** Check the company name and the person's name in the greeting.
7. **Send it yourself** through the employer's website or by email.

If the `README.md` lists writing problems, fix them by hand. They are usually small, such as a long sentence.

## 9. Jobs from LinkedIn, Indeed and StepStone

Those sites do not allow automated search. AutoApp does not scrape them and does not use your login. You can still use them in three ways.

**Option A. Paste the link.** Open a job in your browser. Copy the address. Run:

```bash
autoapp apply-url "https://the-job-link"
```

Use quotes around the link. This works when the page is public and readable. If AutoApp says it could not read the page, use Option B.

**Option B. Save the advert as text.**

1. Copy the whole job advert.
2. Paste it into a new text file named `advert.txt` in the project folder.
3. At the top, add these lines, then one empty line, then the advert:

```
Title: Policy Advisor
Company: Example GmbH
Location: Berlin
URL: https://the-job-link

(the advert text starts here)
```

4. Run:

```bash
autoapp apply-file advert.txt
```

**Option C. Use job alerts as your search.** Create alerts on LinkedIn, Indeed and StepStone for your keywords. They arrive by email. Pick the jobs you like and use Option A or B.

To prepare a package even when the fit check says no, add `--force`:

```bash
autoapp apply-file advert.txt --force
```

## 10. Daily routine

A simple routine that takes about twenty minutes:

1. Open a terminal and switch on the environment (Section 3, Step 4).
2. Make sure your keys are set (Section 4.3).
3. Run `autoapp search` and look at the list.
4. Run `autoapp run --limit 3`.
5. Review the packages (Section 8) and send the ones you are happy with.
6. Add jobs from your LinkedIn, Indeed and StepStone alerts with `apply-url` or `apply-file`.

## 11. Settings you can change

Open `config.yaml` to change how AutoApp works.

```yaml
llm:
  model: claude-opus-5-5
  effort: medium
  web_search: true
sources:
  adzuna:
    enabled: true
  jooble:
    enabled: false
  arbeitnow:
    enabled: true
output_dir: applications
db_path: data/autoapp.db
max_applications_per_run: 5
```

| Setting | Meaning |
|---|---|
| `effort` | `low`, `medium` or `high`. Lower is cheaper and faster. Higher thinks longer. |
| `web_search` | `true` lets the research step search the web. `false` is cheaper but gives less. |
| `sources` | Switch job sources on or off. Jooble needs its own free key in `JOOBLE_API_KEY`. |
| `output_dir` | Folder where packages are saved. |
| `max_applications_per_run` | Upper limit for `autoapp run`. |

## 12. Costs and privacy

**Costs.**
- `autoapp search` is free.
- Each package makes about four calls to the Anthropic API, plus web searches for research. The cost is usually well under one dollar per package. It depends on the effort setting and the advert length.
- Check your spending any time at console.anthropic.com under Usage.
- Start with `--limit 1` or `--limit 3` until you know your typical cost.

**Privacy.**
- Your profile and the job text are sent to Anthropic to produce the research and the documents. Read Anthropic's privacy terms if you are unsure.
- Your keys and profile stay on your computer. They are not uploaded to GitHub, because the project ignores those files.
- Do not put anything in your profile that you would not put on a CV, such as passport numbers.
- Never share your keys. If you think a key leaked, delete it on the provider's site and create a new one.

**Honesty.**
- Send only what you have checked. You are responsible for every statement in an application.
- Some employers ask whether you used AI tools. Answer truthfully. Many universities also have rules about AI use in applications. Check yours.

## 13. Fixing common problems

| What you see | What it means | What to do |
|---|---|---|
| `zsh: command not found: autoapp` | The environment is off, or install failed | `cd ~/AutoApp`, then `source .venv/bin/activate`. If it still fails, run `pip install -e .` again. |
| `does not appear to be a Python project` | You are in the wrong folder | `cd ~/AutoApp` first, then run the command again. |
| `File not found: profile.yaml` | Profile not created, or wrong folder | Be in the AutoApp folder and run `autoapp init`. |
| `command not found: 1671f04e...` (a key) | The key went onto its own line | Type the whole `export NAME=value` on one line. |
| `[skip] Adzuna: set real values` | Keys missing or still placeholders | Set the keys again (Section 4.3). |
| `[warn] adzuna failed: HTTPError HTTP 401` | Adzuna rejected the keys | Copy the App ID and App Key again from the dashboard. |
| `Found 0 jobs` | The sources returned nothing | Broaden keywords, raise `max_age_days`, empty `locations`. |
| `0 with score >= 45` | Threshold too high | Set `min_score` to 25 in `profile.yaml`. |
| `authentication_error` or `invalid x-api-key` | Anthropic key missing or wrong | Set `ANTHROPIC_API_KEY` again, on one line. |
| `credit balance is too low` | No credit on your Anthropic account | Add credit at console.anthropic.com. |
| `The page could not be read` | The job page needs a login or blocks robots | Use `apply-file` with the pasted advert. |
| A YAML error when starting | A spacing or quote mistake in `profile.yaml` | Compare your indents with the example. Put quotes around text that has a colon. |
| Keys are gone after a restart | `export` lasts for one terminal only | Save them in `~/.zshrc` (Section 4.3). |

If you are still stuck, copy the full error text (but never your keys) and ask for help. Hide any key before you paste.

## 14. Updating AutoApp

New features arrive on GitHub. To get them:

```bash
cd ~/AutoApp
git checkout main
git pull origin main
pip install -e .
```

Your profile, settings and finished packages are not changed by an update.

## 15. Words explained

| Word | Meaning |
|---|---|
| Terminal | A window where you type commands. |
| Command | A line you type and run with Enter. |
| Repository | The project folder and its history on GitHub. |
| Clone | Download a repository to your computer. |
| Environment (`.venv`) | A private box for the Python tools AutoApp needs. |
| API key | A private password that lets a program use a service. |
| Environment variable | A named setting, like a key, that lives in your terminal. |
| YAML | The simple text format used for `profile.yaml` and `config.yaml`. |
| Match score | A number from 0 to 100 that shows how well a job fits your profile. |
| Package | The folder of documents AutoApp makes for one job. |
