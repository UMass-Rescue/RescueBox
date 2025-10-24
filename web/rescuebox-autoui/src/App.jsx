// React imports
import {
  Anchor,
  Box,
  Button,
  Grid,
  Group,
  Input,
  MantineProvider,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import "@mantine/core/styles.css";
import { useForm } from "@mantine/form";
import { useEffect, useState } from "react";

// Import CSS
import "./App.css";

// --- NEW SORTING FUNCTION ---
const sortTreeByOrder = (node) => {
  if (node.children && node.children.length > 0) {
    node.children.forEach(sortTreeByOrder); // Recurse first
    node.children.sort((a, b) => (a.order || 0) - (b.order || 0));
  }
  return node;
};
// --- END NEW SORTING FUNCTION ---

// Recursive component to render each group and command
const TreeNode = ({ node, level = 0, onCommandClick }) => (
  <Box pl={level * 16} className={level > 0 ? "tree-indent" : ""}>
    {node.is_group ? (
      <>
        <Text className="tree-group" mt={4} mb={4}>
          {node.name}
        </Text>
        <Stack spacing={0} gap="xs">
          {node.children.map((child, index) => (
            <TreeNode
              key={index}
              node={child}
              level={level + 1}
              onCommandClick={onCommandClick}
            />
          ))}
        </Stack>
      </>
    ) : (
      <Anchor
        href="#"
        className="tree-command"
        onClick={(e) => {
          e.preventDefault();
          onCommandClick(node);
        }}
      >
        <Text mt={2} mb={2}>
          {node.name}
        </Text>
      </Anchor>
    )}
  </Box>
);

const TreeView = ({ tree, onCommandClick }) => (
  <Box className="tree-view-container">
    <TreeNode node={tree} onCommandClick={onCommandClick} />
  </Box>
);

// Main component
const App = () => {
  const [tree, setTree] = useState({});
  const [selectedCommand, setSelectedCommand] = useState(null);
  const [commandOutput, setCommandOutput] = useState("");

  useEffect(() => {
    const treeElement = document.getElementById("tree");
    if (treeElement) {
      const parsedTree = JSON.parse(treeElement.textContent);
      const sortedTree = sortTreeByOrder(parsedTree);
      setTree(sortedTree);
    }
  }, []);

  const handleCommandClick = (command) => {
    setSelectedCommand(command);
    setCommandOutput("");
    // Prefill form values from defaults in schema
    try {
      const defaults = (command?.inputs || []).reduce((values, input) => {
        values[input.name] = input.default ?? "";
        return values;
      }, {});
      form.setValues(defaults);
      form.resetDirty(values => Object.keys(values).length === 0);
    } catch (e) {
      // no-op; safe default if structure differs
    }
  };

  // Initialize form
  const form = useForm({
    initialValues: selectedCommand
      ? selectedCommand.inputs.reduce((values, input) => {
        values[input.name] = input.default || "";
        return values;
      }, {})
      : {},
  });

  const handleRunCommand = async (event) => {
    event.preventDefault(); // Prevent default form submission

    if (!selectedCommand) return;

    const formValues = { ...form.values };
    // console.log(`🔹 With formValues: ${formValues}`);
    const queryParams = new URLSearchParams();

    for (const key in formValues) {
      console.log(`🔹 With key : ${key}`);
      console.log(`🔹 With value : ${formValues[key]}`);
      queryParams.set(key, formValues[key]);
    }

    const isGetRequest =
      selectedCommand.endpoint.includes("/api/routes") ||
      selectedCommand.endpoint.includes("/api/app_metadata") ||
      selectedCommand.endpoint.endsWith("/task_schema");



    if (isGetRequest) {
      queryParams.set("streaming", "false");
    }

    let body = null;
    let url = selectedCommand.endpoint;
    console.log(`🔹 With endpoint : ${url}`);
    let isInternalUrl = false;
    if (isGetRequest) {
      for (const key in formValues) {
        if (Object.prototype.hasOwnProperty.call(formValues, key)) {
          queryParams.set(key, formValues[key]);
        }
      }
      console.log(`🔹 With queryParams : ${queryParams}`);
    } else {
      const inputs = {};
      const parameters = {};
      for (const input of selectedCommand.inputs) {

        if (input.is_parameter) {
          // Always include parameter values; fall back to defaults for hidden fields
          const value = form.values[input.name] ?? input.default ?? "";
          parameters[input.name] = value;
        } else {
          console.log(`🔹 With input fields : ${input.type} ${input.is_file_path}`);
          if (input.type === "str") {
            isInternalUrl = true;
            break;
          }
          if (input.type === "file" || input.type === "directory") {
            let pathValue = form.values[input.name] || ""; // Ensure it's a string, even if empty
            // Remove leading/trailing quotes if present
            if (typeof pathValue === 'string' && pathValue.startsWith('"') && pathValue.endsWith('"')) {
              pathValue = pathValue.substring(1, pathValue.length - 1);
            }
            inputs[input.name] = { path: pathValue }; // Always include the field
          } else if (input.type === "text") {
            const textValue = form.values[input.name] || ""; // Ensure it's a string, even if empty
            inputs[input.name] = { text: textValue }; // Always include the field
          }
        }
      }
      if (!isInternalUrl && Object.keys(inputs).length > 0) {
        body = JSON.stringify({ inputs: inputs, parameters: parameters });
      } else {
        body = null;
      }
      console.log(`🔹 With body: ${body}`);
    }

    const queryString = queryParams.toString();
    if (queryString && isInternalUrl) {
      url = `${url}?${queryString}`;
    }

    console.log(
      `🔹 Sending ${isGetRequest ? "GET" : "POST"} request to: ${url}`
    );
    setCommandOutput(""); // Reset output

    try {
      const response = await fetch(url, {
        method: isGetRequest ? "GET" : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: body,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! Status: ${response.status} - ${JSON.stringify(errorData)}`);
      }

      const rawText = await response.text();
      console.log("🔹 Raw response from server:", rawText);

      let parsedData;
      try {
        parsedData = JSON.parse(rawText); // Try parsing as JSON
      } catch (jsonError) {
        console.warn("⚠️ Server returned plain text instead of JSON.");
        parsedData = rawText; // Use raw text if JSON parsing fails
      }

      setCommandOutput(
        typeof parsedData === "object"
          ? JSON.stringify(parsedData, null, 2)
          : parsedData.toString()
      );
    } catch (error) {
      console.error("❌ Request failed:", error);
      setCommandOutput(`❌ Error: ${error.message}`);
    }
  };

  const handleReset = () => {
    if (selectedCommand) {
      setSelectedCommand("");
      setCommandOutput("");
      form.reset();
    }
  };

  return (
    <MantineProvider>
      <Grid grow>
        {/* Left Panel: Command Tree */}
        <Grid.Col span={4} className="grid-column">
          <Text
            size="xl"
            weight={700}
            mt={0}
            mb={12}
            className="tree-view-title"
          >
            Rescuebox CLI
          </Text>
          <TreeView tree={tree} onCommandClick={handleCommandClick} />
        </Grid.Col>

        {/* Right Panel: Command Details and Output */}
        <Grid.Col span={8} className="grid-column">
          {selectedCommand ? (
            <>
              <Group justify="space-between" mb={8}>
                <Text size="xl" weight={600}>
                  {selectedCommand.name}
                </Text>
                <Button variant="light" onClick={handleReset}>
                  Reset
                </Button>
              </Group>
              <Text mb={12} color="dimmed">
                {selectedCommand.help || "No description available."}
              </Text>

              {/* Command Form */}
              <form onSubmit={handleRunCommand} className="command-form">
                <Stack spacing="xs" mb={12}>
                  {(selectedCommand.inputs || [])
                    .filter((input) => {
                      if (!input.is_parameter) return true;
                      // Hide these parameter fields from UI; use defaults instead
                      return !(
                        input.name === "model_name" ||
                        input.name === "chunker" ||
                        input.name === "chunk_size" ||
                        input.name === "chunk_overlap"
                      );
                    })
                    .map((input) => {
                      const isLockedParam =
                        !!input.is_parameter &&
                        (input.name === "model_name" || input.name === "chunker");
                      return (
                        <Box key={input.name}>
                          {input.help && (
                            <Text size="sm" color="dimmed" mb={4}>
                              {input.help}
                            </Text>
                          )}
                          {(input.type === "str" ||
                            input.type === "text" ||
                            input.type === "file" ||
                            input.type === "directory") && (
                              <Input
                                placeholder={input.default || ""}
                                {...form.getInputProps(input.name)}
                                required={!isLockedParam}
                                disabled={isLockedParam}
                              />
                            )}
                          {(input.type === "int" || input.type === "ranged_int") && (
                            <Input
                              type="number"
                              placeholder={input.default?.toString() || ""}
                              {...form.getInputProps(input.name)}
                              required
                            />
                          )}
                          {(input.type === "float" || input.type === "ranged_float") && (
                            <Input
                              type="float"
                              placeholder={input.default?.toString() || ""}
                              {...form.getInputProps(input.name)}
                              required
                            />
                          )}
                          {input.type === "enum" && (
                            <Input
                              placeholder={input.default || ""}
                              {...form.getInputProps(input.name)}
                              required={!isLockedParam}
                              disabled={isLockedParam}
                            />
                          )}
                        </Box>
                      );
                    })}
                  <Button type="submit">Run Command</Button>
                </Stack>
              </form>

              {/* Command Output */}
              <Text mt={16} mb={4} weight={500}>
                Command Output:
              </Text>
              <Textarea
                value={commandOutput}
                readOnly
                minRows={10}
                className="command-output"
              />
            </>
          ) : (
            <Text>Select a command from the left panel to see details</Text>
          )}
        </Grid.Col>
      </Grid>
    </MantineProvider>
  );
};

export default App;