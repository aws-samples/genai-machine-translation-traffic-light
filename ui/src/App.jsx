// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import * as React from "react";
import { useState } from "react";
import { useEffect } from "react";
import PropTypes from "prop-types";
import { Amplify, API, Storage } from "aws-amplify";
import { withAuthenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import AppLayout from "@cloudscape-design/components/app-layout";
import ContentLayout from "@cloudscape-design/components/content-layout";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Header from "@cloudscape-design/components/header";
import TextContent from "@cloudscape-design/components/text-content";
import Button from "@cloudscape-design/components/button";
import Textarea from "@cloudscape-design/components/textarea";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import RadioGroup from "@cloudscape-design/components/radio-group";
import Select from "@cloudscape-design/components/select";
import Modal from "@cloudscape-design/components/modal";
import Box from "@cloudscape-design/components/box";
import FormField from "@cloudscape-design/components/form-field";
import Slider from "@cloudscape-design/components/slider";
import Input from "@cloudscape-design/components/input";

import awsExports from "./aws-exports";

Amplify.configure(awsExports);

const App = ({ signOut }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [source, setSource] = useState("16 Penn State in which redshirt freshman Jim Kelly threw for 280 yards and three touchdowns in his first career start as Miami's quarterback.");
  const [translation, setTranslation] = useState("16 Penn State, in dem Rothemd-Neuling Jim Kelly warf 280 Meter und drei Touchdowns in seiner ersten Karriere starten als Miami Quartier zurück.");
  const [llm, setLLM] = useState({label: "Claude 3 Sonnet", value: "claude3" });
  const [temperature, setTemp] = useState(0);
  const [visible, setVisible] = useState(false);
  const [language, setLanguage] = useState("german");
  const [rating, setRating] = useState("");
  const [reason, setReason] = useState("");
  const [errors, setErrors] = useState([]);
  const [promptList, setPromptList] = useState([]);
  const [promptView, setPromptView] = useState({label: "Select a Prompt", value: "" });
  const [promptText, setPromptText] = useState("")


  const submitQuery = async () => {
    try {
      setIsSubmitting(true);
      const response = await API.post("api", "/", { body: { source, translation, llm, language, temperature }, headers: { "Content-Type": "text/plain" } });
      const parsedResponse = JSON.parse(response);

      console.log("Raw Response: ", response);
      console.log("Parsed Parsed Response: ", parsedResponse);
      console.log("Rating: ", parsedResponse.rating);
      console.log("Reason: ", parsedResponse.reason);
      console.log("Errors: ", parsedResponse.errors);
      setRating(parsedResponse.rating);
      setReason(parsedResponse.reason);
      setErrors(parsedResponse.errors);
      setIsSubmitting(false);
    } catch (error) {
      console.log("Error Occured", error)
      setIsSubmitting(false);
    }
  }

  useEffect(() => {
    const fetchData = async () => {
    const promptResponse = await API.post("api", "/");
    const promptListItems = promptResponse.items
    console.log("Raw Prompt Response: ", promptResponse);
    console.log("Prompt List: ", promptListItems);
    setPromptList(promptListItems)
    }
    fetchData()
    }, [])

  return (
    <>
      <Modal
        onDismiss={() => setVisible(false)}
        visible={visible}
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button 
                variant="link"
                onClick={() => {setVisible(false)}}
              >
                Cancel
              </Button>
              <Button 
                variant="primary"
                onClick={() => {setVisible(false)}}
              >
                Save
              </Button>
            </SpaceBetween>
          </Box>
        }
        header="Prompt Viewer"
      >
        <SpaceBetween size="xs">
          <Select
            selectedOption={promptView}
            onChange={({ detail }) => setPromptView(detail.selectedOption)}
            options={
              promptList
            }
          />
          <TextContent>
            <div style={{ display: 'block' }}>
              {"Prompt:"}
            </div>
          </TextContent>
          <Textarea
            rows={40}
            onChange={({ detail }) => setPromptText(detail)}
            value={promptView.value}
            placeholder="Prompt..."
            disableBrowserSpellcheck
          />
        </SpaceBetween>
      </Modal>
    <AppLayout
      contentType="dashboard"
      navigationHide={true}
      toolsHide={true}
      content={
        <ContentLayout
          header={
            <SpaceBetween size="xl">
              <Header
                variant="h1"
                description="Rate the quality of machine translation output (English -> German/French Preview)."
                actions={
                  <SpaceBetween direction="horizontal" size="xs">
                    <Button
                      onClick={signOut}
                    >
                      Sign out
                    </Button>
                  </SpaceBetween>
                }
              >
                Machine Translation Quality Assessment For Language Line
              </Header>
            </SpaceBetween>
          }
        >
          <SpaceBetween size="s">
            <Textarea
              onChange={({ detail }) => setSource(detail.value)}
              value={source}
              placeholder="Source language content..."
              rows={2}
            />
            <Textarea
              onChange={({ detail }) => setTranslation(detail.value)}
              value={translation}
              placeholder="Translation..."
              rows={2}
            />
            <SpaceBetween direction="horizontal" size="xl">
              <Select
                selectedOption={llm}
                onChange={({ detail }) => setLLM(detail.selectedOption)}
                options={[
                  { label: "Claude 3 Sonnet", value: "claude3" },
                  { label: "Llama 2 70B", value: "llama2" }
                ]}
              />
              <RadioGroup
                onChange={({ detail }) => setLanguage(detail.value)}
                value={language}
                items={[
                  { value: "german", label: "English -> German" },
                  { value: "french", label: "English -> French" }
                ]}
              />

              <FormField label="Temperature">
                <div className="flex-wrapper">
                  <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTemp(detail.value)}
                    value={temperature}
                    max={1}
                    min={0}
                    step={0.1}
                    tickMarks
                  />
                  </div>
                  <SpaceBetween
                    size="m"
                    alignItems="center"
                    direction="horizontal"
                  >
                    <div className="input-wrapper">
                      <Input
                        type="number"
                        inputMode="decimal"
                        value={temperature.toString()}
                        onChange={({ detail }) => {
                          setTemp(Number(detail.value));
                        }}
                        controlId="validation-input"
                        step={0.1}
                        placeholder="0.0"
                      />
                    </div>
                  </SpaceBetween>
                </div>
              </FormField>
              <Button
                variant="primary"
                onClick={() => setVisible(true)}
              >
                View Prompt
              </Button>
              <Button
                variant="primary"
                onClick={submitQuery}
                loading={isSubmitting}
              >
                Assess Quality
              </Button>
            </SpaceBetween>
            <TextContent>
              <h2>Output:</h2>
            </TextContent>

            <StatusIndicator type={rating === "RED"
              ? "error"
              : rating === "AMBER"
                ? "warning"
                : rating === "GREEN"
                  ? "success"
                  : "info"}>
              {rating === "RED"
                ? "RED: Significant Errors"
                : rating === "AMBER"
                  ? "AMBER: Requires Corrections"
                  : rating === "GREEN"
                    ? "Green: No Corrections"
                    : ""}
            </StatusIndicator>
            <SpaceBetween direction="horizontal" size="s">
              <TextContent>
                <h2>Reason:</h2>
                <div style={{ display: 'block' }}>
                  {reason}
                </div>
              </TextContent>
            </SpaceBetween>
            <SpaceBetween direction="horizontal" size="s">
              <TextContent>
                <h2>Errors:</h2>
                <ul>
                  {errors?.map(err => (
                    <li key={err}>
                      {err}
                    </li>
                  ))}
                </ul>
              </TextContent>
            </SpaceBetween>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  </>
  );
}

App.propTypes = {
  signOut: PropTypes.func.isRequired,
};

const AuthApp = withAuthenticator(App, { hideSignUp: true })

export default AuthApp;
