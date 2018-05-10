How to run:
  python sqaTools.py or run run.bat

How to build exe:
  1.Modify run_bruce.spec
  2.run pyinstaller_exe.bat
    or if you want to generate exe and zip all project, then:
      python build.py
      
How to change project version, host etc.:
  Open data/app.json:
      {
        "name": "sqaTools",
        "version": "1.1.3",
        "host": "127.0.0.1",
        "port": 5000
      }
