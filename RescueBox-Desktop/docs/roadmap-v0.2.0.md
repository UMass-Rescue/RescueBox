# Roadmap for v0.1.0

## UI Functional Requirements

- Info page : render markdown that u receive. [https://github.com/remarkjs/react-markdown]

  - { info: string }

- Schema Parser into input page

  - Fix input and output box:
    - inputs: [ { key:string, label: string, subtitle?: string, type: string_enum[file, folder, text] } ],
    - parameters: { key: string, label: string, subtitle?: string, value: { type: ranged_float, range: {min: float, max: float}, default: float} | { type: float } | {type: enum, enum_vals: {label: string, key: string}[], default: string} | { type: text } } | { type: ranged_int, range: {min: int, max: int}, default: int} | { type: 'int' }

- Template output page for each format
  - Broad categories: 1. File type (image file, csv file, json file, txt file, audio file, video file), Dir type, Data blob
  - { output_type: "file", file_type: 'img' | 'csv' | 'json' | 'text' | 'audio' | 'video', file_path: string, title: string, subtitle?: string }
    { output_type: "directory", file_path: string, title: string, subtitle?: string }
    | { output_type: "markdown", value: string }

## Backend Requirements

## General Requirements
