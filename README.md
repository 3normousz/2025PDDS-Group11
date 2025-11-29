# 2025PDDS-Group11

**How to run this thing**

1. Create and activate a virtual environment
* You can just copy and paste it into the terminal, make sure that the terminal is where your project is.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies
* Same as above
```powershell
pip install -r requirements.txt
```

3. (Optional) If you need to use Tailwind CSS (https://tailwindcss.com/docs/styling-with-utility-classes)
* Create another terminal (the '+' icon in the terminal tab if you use VS Code), and just copy these.

* This will make changes you make related to Tailwind updated real-time. You should use this, I think it would be much easier compared to pure CSS. But it's purely optional, you can skip this.

```powershell
npm install
npx tailwindcss -i ./static/src/input.css -o ./static/src/output.css --watch
```

4. Run the app
* Go back to previous powershell, or create a new one is fine.

```powershell
python main.py
```

Open your browser at `http://localhost:5000`


**Project layout**

- `main.py` - application entrypoint (the web server)
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates used by the web app
- `data/` - dataset used in our project.
* For these 2 below, you don't need to really worry about.
- `static/` - static assets (CSS, images, built frontend files)
- `static/src/` - source CSS for Tailwind (`input.css`, `output.css`)

**Development tips**
- If the app fails to start, ensure that the virtual environment is activated when installing/running  (Step 1 in 'Requirements').
- If you wanted to make changes, you can add a new route (on "main.py", you can refer to the existing one) and make new .html files in the "templates" folder. And I will combine every routes you guys make into 1 single dashboard
