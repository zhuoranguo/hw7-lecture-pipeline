# Homework 7: Agentic Video Lecture Pipeline

This repository implements the [Homework 7](https://zlisto.github.io/genAI_social_media/hw7.html) pipeline: a PDF slide deck is rasterized, described and narrated with Gemini (multi-stage agents), synthesized to speech with [edge-tts](https://github.com/rany2/edge-tts), and assembled into one `.mp4` with **[MoviePy](https://zulko.github.io/moviepy/)** (encoding uses the FFmpeg binary bundled via `imageio-ffmpeg`—no separate system FFmpeg install).

## Prerequisites

- **Python 3.10+**
- A **Gemini API key** (`GEMINI_API_KEY` or `GOOGLE_API_KEY` in the environment or a `.env` file)

Optional: override the vision/text model with `GEMINI_MODEL` (default `gemini-2.0-flash`).

You may see a `FutureWarning` from `google.generativeai`; the package still works for this assignment. Migrate to `google.genai` later if you want to silence it.

## Setup

```bash
cd /path/to/hw7-lecture-pipeline
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repo root (do **not** commit it):

```bash
GEMINI_API_KEY=your_key_here
```

Place **`Lecture_17_AI_screenplays.pdf`** in the repository root (required for grading). If you do not have it yet, the first run can fetch it:

```bash
python run_lecture_pipeline.py --fetch-missing
```

The default instructor transcript is [Lecture 11 Section 2 captions](https://zlisto.github.io/genAI_social_media/slides_pdf/MGT%20575%2001-02%20(SP26)_%20%20Generative%20AI%20and%20Social%20Media%20Lecture%2011%20Section%202_Captions_English%20(United%20States).txt); `--fetch-missing` saves it as `Lecture_11_Section_2_Captions.txt` next to the PDF.

## Run the full pipeline

```bash
python run_lecture_pipeline.py --fetch-missing
```

Stages (in order):

1. **Style** — reads the transcript → `style.json` at the repo root  
2. **Project folder** — `projects/project_YYYYMMDD_HHMMSS/`  
3. **Slides** — PDF → `slide_images/slide_001.png`, …  
4. **Slide description agent** — chained vision calls → `slide_description.json`  
5. **Premise agent** → `premise.json`  
6. **Arc agent** → `arc.json`  
7. **Narration agent** — title slide gets intro + topic overview → `slide_description_narration.json`  
8. **TTS** → `audio/slide_001.mp3`, … (long narrations are chunked, then merged per slide)  
9. **Video** (MoviePy) → `Lecture_17_AI_screenplays.mp4` inside the project folder  

### Resume / partial runs

Reuse an existing project and skip completed stages, for example:

```bash
python run_lecture_pipeline.py \
  --project-dir projects/project_20260409_120000 \
  --skip-style --skip-slides --skip-premise --skip-arc \
  --skip-narration
```

(List voices: `edge-tts --list-voices`; set e.g. `--tts-voice en-US-JennyNeural`.)

## Grading rubric alignment (Homework 7)

| # | Points | Requirement | How this repo satisfies it |
|---|--------|-------------|---------------------------|
| 1 | 8 | Style from **Lecture 11 Section 2** transcript → **`style.json`** at repo root | `run_lecture_pipeline.py` reads `--transcript` (default `Lecture_11_Section_2_Captions.txt`, same source as the [official .txt](https://zlisto.github.io/genAI_social_media/slides_pdf/MGT%20575%2001-02%20(SP26)_%20%20Generative%20AI%20and%20Social%20Media%20Lecture%2011%20Section%202_Captions_English%20(United%20States).txt)) and `lecture_agents/style_agent.py` writes **`style.json`**. A committed placeholder is overwritten on a full run (do not use `--skip-style` for a fresh grading run). |
| 2 | 18 | Rasterized deck + **current slide image** + **all previous descriptions** in context → **`slide_description.json`** | `pdf_raster.py` creates **`slide_images/slide_NNN.png`**. `slide_description_agent.py` calls the vision model with **each PNG** and a prompt that embeds **every prior slide’s description** in full (not a trivial summary). |
| 3 | 10 | Entire **`slide_description.json`** → **`premise.json`** | `premise_agent.py` loads the full file into the prompt (only capped if the file exceeds a very large safety limit in `doc_truncation.py`). |
| 4 | 10 | **`premise.json`** + **`slide_description.json`** → **`arc.json`** | `arc_agent.py` loads both documents into the prompt (same truncation policy for oversized inputs). |
| 5 | 18 | **Current image** + **`style.json`**, **`premise.json`**, **`arc.json`**, **`slide_description.json`**, **prior narrations** → **`slide_description_narration.json`**; **title slide** intro + overview | `narration_agent.py` uses a **dedicated title-slide prompt** for **`slide_index == 1`** (instructor intro + topic overview). Other slides use prior narration text in the prompt and attach the **current slide image**. Output lists **`description`** and **`narration`** per slide. |
| 6 | 14 | Narration strings → **`audio/slide_NNN.mp3`**; **merge chunks** per slide if needed | `tts_step.py` reads **`slide_description_narration.json`**, names files **`slide_001.mp3`**, etc. Long lines are split into **multiple edge-tts requests** and the MP3s are **concatenated** into **one file per slide** via MoviePy’s **`concatenate_audioclips`**. |
| 7 | 12 | Matching **PNG** + **MP3** indices → one **`.mp4`** whose basename matches the **PDF**; segment length follows audio | `video_assembly.py` pairs **`slide_images/slide_NNN.png`** with **`audio/slide_NNN.mp3`**, sorts by **`slide_index`**, sets each still’s duration to **that MP3’s length** (no long silent tail), concatenates into **`{pdf_stem}.mp4`** next to the project JSON (same basename as `Lecture_17_AI_screenplays.pdf`). |
| 8 | 10 | Code + **README** + project **JSON**; **no** committed PNG/MP3/MP4 | **`.gitignore`** excludes generated media under **`projects/`**. Submit **code**, **`requirements.txt`**, **`README.md`**, committed **`style.json`**, and place **`Lecture_17_AI_screenplays.pdf`** at the repo root. After a local run you may commit the **`projects/project_…/*.json`** artifacts for the grader if your course allows (media stays ignored). |

## Layout

```
├── README.md
├── style.json                 # placeholder until style stage runs; then transcript-derived
├── Lecture_17_AI_screenplays.pdf
├── requirements.txt
├── run_lecture_pipeline.py
├── lecture_agents/
└── projects/
    └── project_YYYYMMDD_HHMMSS/
        ├── slide_images/      # gitignored PNGs
        ├── audio/             # gitignored MP3s
        ├── *.mp4              # gitignored
        ├── premise.json
        ├── arc.json
        ├── slide_description.json
        └── slide_description_narration.json
```

Per the assignment, **do not commit** generated images, audio, or video; `.gitignore` is set accordingly. Commit code, `requirements.txt`, **`style.json`**, and this README; add **`Lecture_17_AI_screenplays.pdf`** at the root before submission. Each run creates **`projects/project_YYYYMMDD_HHMMSS/`** with empty **`slide_images/`** and **`audio/`** immediately, then fills them when raster + TTS run.
