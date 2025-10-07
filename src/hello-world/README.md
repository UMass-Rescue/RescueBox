### Steps to create a RescueBox plugin

1 refer the hello_world main.py for a sample plugin. 
        implement all these functions as per doc https://github.com/UMass-Rescue/RescueBox/wiki/README%E2%80%90Plugins

2. implement tests as in tests\test_main.py

3. In `rescuebox/plugins/__init__.py`, add your app to the list of `plugins`. Example:
```python
from text_summary.main import app as text_summary_app, APP_NAME as text_summary_app_name

# Adding the following to the list of plugins in the "plugins" variable
RescueBoxPlugin(text_summary_app, text_summary_app_name, "Text summarization library"),
```

4 update dependencies in top level pyproject.toml , with exact versions . in the package level pyproject.toml use wildcard
   this means that: all plugins will use the same version as in top level pyproject.toml.
