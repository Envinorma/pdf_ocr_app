# OCR utils

[![Build Status](https://github.com/envinorma/ocr_utils/workflows/Test%20and%20Lint/badge.svg)](https://github.com/envinorma/ocr_utils/actions)
[![Code Coverage](https://codecov.io/gh/envinorma/pdf_ocr_app/branch/main/graph/badge.svg)](https://codecov.io/gh/envinorma/pdf_ocr_app)

A ready-to-deploy Dash application for parsing PDF files with Tesseract

## Features

- Performs OCR on user uploaded PDF documents
- Displays low level tesseract-OCR results
- Enables SVG download
  [Example app here](https://pdf-envinorma.herokuapp.com/)

## Quick Start

```bash
git clone git@github.com:Envinorma/pdf_ocr_app.git
cp pdf_ocr_app
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cp config-template.ini config.ini # Adapt configuration
python pdf_ocr_app/app/__init__.py # Visit http://127.0.0.1:8050/
```

## Deploy on heroku

```bash
heroku git:remote -a $app_name
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
git push heroku master
```

**MIT license**
