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
  const [isPolling, setIsPolling] = useState(false);
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
    setIsPolling(false);
  };

  // Initialize form
  const form = useForm();

  // NEW: This effect updates the form whenever a new command is selected.
  useEffect(() => {
    if (selectedCommand) {
      form.setValues(
        selectedCommand.inputs.reduce((values, input) => {
          values[input.name] = input.default || "";
          return values;
        }, {})
      );
    } else {
      form.reset();
    }
  }, [selectedCommand]);

  // NEW: Function to poll for the result of an async task
  const pollForResult = async (resultUrl) => {
    console.log(`Polling for result from: ${resultUrl}`);
    try {
      const resultResponse = await fetch(resultUrl, { method: "GET" });
      if (!resultResponse.ok) {
        const errorData = await resultResponse.json();
        throw new Error(`HTTP error! Status: ${resultResponse.status} - ${JSON.stringify(errorData)}`);
      }

      const resultData = await resultResponse.json();
      console.log("🔹 Polling response:", resultData);

      // Check if the task is still pending by looking for the 'status' title
      if (resultData && resultData.title === "status" 
            && resultData.value === 'Task status: PENDING') {
        setCommandOutput(
          (prevOutput) => prevOutput + ` ${resultData.value}`
        );
        // Poll again after a 5-second delay
        setTimeout(() => pollForResult(resultUrl), 5000);
      } else {
        // Task is done (or failed), display the final result
        setCommandOutput(
          typeof resultData === "object"
            ? JSON.stringify(resultData, null, 2)
            : resultData.toString()
        );
        setIsPolling(false); // Stop polling
      }
    } catch (error) {
      console.error("❌ Polling failed:", error);
      setCommandOutput((prevOutput) => prevOutput + `\n❌ Polling Error: ${error.message}`);
      setIsPolling(false); // Stop polling on error
    }
  };

  const handleRunCommand = async (event) => {
    event.preventDefault(); // Prevent default form submission
    if (!selectedCommand || isPolling) return; // NEW: Prevent running if already polling

    // if (!selectedCommand) return;

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
          parameters[input.name] = formValues[input.name];
        } else {
          console.log(`🔹 With input fields : ${input.type} ${input.is_file_path}`);
          if (input.type === "str") {
            isInternalUrl = true;
            break;
          }
          if (input.type === "file" || input.type === "directory") {
            let pathValue = formValues[input.name] || ""; // Ensure it's a string, even if empty
            // Remove leading/trailing quotes if present
            if (typeof pathValue === 'string' && pathValue.startsWith('"') && pathValue.endsWith('"')) {
              pathValue = pathValue.substring(1, pathValue.length - 1);
            }
            inputs[input.name] = { path: pathValue }; // Always include the field
          } else if (input.type === "text") {
            const textValue = formValues[input.name] || ""; // Ensure it's a string, even if empty
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

      let parsedData = rawText;
      try {
        parsedData = JSON.parse(rawText); // Try parsing as JSON
      } catch (jsonError) {
        console.warn("⚠️ Server returned plain text instead of JSON. ${jsonError}");
        parsedData = rawText; // Use raw text if JSON parsing fails
      }
      
      console.log("🔹 Parsed response from server:", parsedData);
      console.log("🔹 Parsed response title:", parsedData.title);
      console.log("🔹 Parsed response taskId:", parsedData.value);
      // NEW: Check for a task_id in the response to start polling
      if (
        parsedData &&
        parsedData.title === "task_id"
      ) {
        const taskId = parsedData.value;
        const resultUrl = `${selectedCommand.endpoint}/result/${taskId}`;
        
        setCommandOutput(`Task started with ID: ${taskId}. Polling for result...`);
        setIsPolling(true);
        pollForResult(resultUrl); // Start polling for the result
      } else {
        // This is a synchronous command, display the result directly
        setCommandOutput(
          typeof parsedData === "object"
            ? JSON.stringify(parsedData, null, 2)
            : parsedData.toString()
        );
      }
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
                  {selectedCommand.inputs.map((input) => {
                    return (
                      <Box key={input.name}>
                        {input.help && (
                          <Text size="sm" color="dimmed" mb={4}>
                            {input.help}
                          </Text>
                        )}
                        {(input.type === "str" ||
                          input.type === "text" ||
                          input.type === "file" || // Added for file inputs
                          input.type === "directory") && ( // Added for directory inputs
                            <Input
                              placeholder={input.default || ""}
                              {...form.getInputProps(input.name)}
                              required
                            />
                          )}
                        {(input.type === "int" ||
                          input.type === "ranged_int") && (
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
                            required
                          />
                        )}
                      </Box>
                    );
                  })}
                  {/* NEW: Disable button while polling */}
                  <Button type="submit" disabled={isPolling}>
                    {isPolling ? "Polling for Result..." : "Run Command"}
                  </Button>
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