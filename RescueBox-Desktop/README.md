[![Build Status][github-actions-status]][github-actions-url]
[![Github Tag][github-tag-image]][github-tag-url]

# RescueBox Desktop

<img align="right" width="200" src="./docs/icon.png" width="200" />

RescueBox Desktop (RBox) is a self-contained binary offering a UI interface to a library of ML models for various forensic applications. To use RescueBox Desktop, start up a model application in the background adhering to the [Fastapi](https://github.com/UMass-Rescue/RescueBox/blob/main/flaskml_migration_steps.md) interface.  You can now run the model [server](https://github.com/UMass-Rescue/RescueBox/blob/main/run_server) and interact by specifying its inputs on the UI and analyzing outputs when ready. RBox handles the rest: running the jobs, and interfacing with different ML models. Since RBox is aimed toward forensic analysts, it is designed to operate on local, or drive-mounted storage.

For a review of the project's goals, read [What is RescueBox Desktop?](./docs/what-is-rescuebox-desktop.md). For a view into how RBox-Desktop works, read the [architecture section](#architecture).

# Getting Started

## Step 1: Download the Latest Release

Get the latest release of the binary for your operating system (Windows) from the [source](https://github.com/UMass-Rescue/RescueBox/tree/main/RescueBox-Desktop).

## Step 2: Start a Fastapi Compliant Model

Download and run the [Fastapi](https://github.com/UMass-Rescue/RescueBox/wiki/Onboarding) model server.

Run the model application server, which should provide you with a URL to RBox.

## Step 3: Using the App
Launch the Rescuebox-Desktop icon or see below to launch in dev mode using npm start.

You should now be able to see the model application in the app, and be able to run inference tasks on it!

![](./docs/ui-screenshot.png)

## Additional Instructions for Mac


Might need these before `npm install`
```
### Upgrade node if your node version is less than 14. (check with `node -v`)
brew install node@20
echo 'export PATH="/usr/local/opt/node@20/bin:$PATH"' >> ~/.zshrc

### Install python-setuptools since we're using python 3.12
brew install python-setuptools
### Or install it from https://pypi.org/project/setuptools/ into the python environment on your command line
```

9.  Install UI dependencies
```
cd RescueBox-Desktop
npm install
```

10. Run UI
```
npm start
```

You should see the UI show up after this. Connect to your server and go to the "Models" tab to run the models.
```
# Development

RescueBox Desktop is built using [Electron](https://www.electronjs.org/), [React](https://reactjs.org/), TypeScript, TailwindCSS, and SQlite (with Sequelize).


## Prerequisites

- Node v18 (newer versions may work)

## Install

Clone the repo and install dependencies:

```bash
git clone https://github.com/UMass-Rescue/RescueBox.git
cd RescueBox-Desktop
npm install
```

**Having issues installing? See this [debugging guide](https://github.com/electron-react-boilerplate/electron-react-boilerplate/issues/400)**

## Starting Development

Start the app in the `dev` environment:

```bash
npm start
```

## Packaging for Production

To package apps for the local platform:

```bash
1 build the rescuebox.exe using the rescuebox.spec in RescueBox directory. ( see file for instructions)

2 copy pre reqs to assets\rb_server : 
winfsp-2.0.23075.msi , docs , demo files to run models

3 copy these cmds to rb.bat and run it as one batch file
rmdir /s /q assets\rb_server\dist
move ../dist assets\rb_server
cmd /c npm cache clean --force
cmd /c npm cache verify
cmd /c npm install
cmd /c npm run postinstall
cmd /c npm run build
cmd /c npm run rebuild
cmd /c npm exec electron-builder -- --win
```
note : release\app\package.json contains the version number

4 release\build\RescueBox-Desktop Setup 2.0.0.exe should get created
 

## Docs

See electron-react's [docs and guides here](https://electron-react-boilerplate.js.org/docs/installation)


