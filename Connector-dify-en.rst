Connector - Dify
----------------
The following integration methods are available for Dify:

- Part 1 - Using the F5 Guardrails model plugin from the Dify Marketplace
- Part 2 - Using Dify's built-in OpenAI compatible model plugin to call the F5 Guardrails OpenAI compatible API
- Part 3 - Using Dify's Moderation API to call the F5 Guardrails Scans endpoint
- Part 4 - Using an "HTTP Request" node in a Workflow to call the F5 Guardrails Scans endpoint
- Part 5 - Using the F5 Guardrails tool node in a Workflow to call the F5 Guardrails Scans endpoint


Part 1 - Using the F5 Guardrails model plugin from the Dify Marketplace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method integrates F5 Guardrails by directly installing its model plugin from the Dify Marketplace. After installation, users can configure the relevant Project/Provider settings from F5 Guardrails. The plugin wraps the F5 Guardrails Prompts API as a model, enabling users to call F5 Guardrails functionality directly within Dify to scan input and output content. This is therefore an Inline mode integration.

Step 1 - Install the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Click "Plugins" in the top-right corner of the Dify interface, then click "Explore Marketplace" in the panel that appears. Search for "F5" in the Marketplace, locate the plugin, and click to install it.

..  image:: ./_static/integration-Dify-01.png

..  Note::

   For full details about this plugin, visit https://marketplace.dify.ai/plugin/f5/f5_guardrail

Step 2 - Configure the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After installation, click the user avatar in the top-right corner and select "Settings". In the Settings page, choose "Model Provider", locate the installed F5 Guardrails plugin, and click "Add API Key" to enter the plugin configuration interface. Follow the on-screen prompts to complete the configuration:

..  image:: ./_static/integration-Dify-02.png

Step 3 - Use the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^
Once configured, you can select the F5 Guardrails model as the LLM Provider directly in the Dify App orchestration interface, as shown below:

..  image:: ./_static/integration-Dify-03.png


Part 2 - Using Dify's built-in OpenAI compatible model plugin to call the F5 Guardrails OpenAI compatible API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method calls the F5 Guardrails OpenAI compatible API through Dify's own OpenAI compatible model plugin. Users need to install the OpenAI compatible model plugin in Dify and configure it to point to the F5 Guardrails OpenAI compatible API endpoint. Once configured, users can use this model plugin within Dify to invoke F5 Guardrails functionality.

.. Note::

   When F5 Guardrails triggers a blocking response, the returned API format is non-OpenAI compliant. A transparent proxy must therefore be deployed to handle these non-OpenAI format responses. The URL entered in Step 2 below should be the URL of this transparent proxy.
   The transparent proxy service can be obtained here: https://github.com/f5se/openai-f5-guardrail-api-converter

Step 1 - Install the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Click "Plugins" in the top-right corner of the Dify interface, then click "Explore Marketplace" in the panel that appears. Search for "OpenAI" in the Marketplace, locate the OpenAI compatible model plugin provided by Dify, and click to install it.

..  image:: ./_static/integration-Dify-04.png

Step 2 - Configure the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Click "Settings" in the top-right corner of the Dify interface. In the Settings page, choose "Model Provider", locate the installed OpenAI compatible model plugin, and click "Add Model" to enter the plugin configuration interface. Follow the on-screen prompts to complete the configuration:

..  image:: ./_static/integration-Dify-05.png

Step 3 - Use the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^
Once configured, you can select the F5 Guardrails model as the LLM Provider directly in the Dify App orchestration interface, as shown below:

..  image:: ./_static/integration-Dify-06.png

- Part 3 - Using Dify's Moderation API to call the F5 Guardrails Scans endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method calls the F5 Guardrails Scans endpoint through Dify's Moderation API. Users need to separately deploy a service interface that conforms to the Dify Moderation API specification, and then configure the Moderation API within the Dify App.
The Moderation API service source code is available at `Github repo <https://github.com/f5se/openai-f5-guardrail-api-converter>`_

Step 1 - Configure the API Extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Click "Settings" in the top-right corner of the Dify interface. In the Settings page, select "API Extension" and click "Add API Extension" to enter the configuration interface. Follow the on-screen prompts to complete the configuration:

..  image:: ./_static/integration-Dify-07.png

Step 2 - Configure Content Moderation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Within a specific App — typically a chat application — locate "Enable feature to enhance web app user experience" at the bottom of the app debugging interface. Click it and enable "Content moderation". In the Moderation API configuration interface, select the previously configured API Extension to complete the setup.

..  image:: ./_static/integration-Dify-08.png

Step 3 - Test and Verify
^^^^^^^^^^^^^^^^^^^^^^^^^
Select an LLM that has not been routed through Guardrails in the application, conduct a conversation test, and observe whether sensitive content is correctly identified and handled.

..  image:: ./_static/integration-Dify-09.png


- Part 4 - Using an "HTTP Request" node in a Workflow to call the F5 Guardrails Scans endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a Workflow, you can add an "HTTP Request" node and configure its request URL to point to the F5 Guardrails Scans API, enabling scanning of input and output content. Users can flexibly use this HTTP Request node to call the F5 Guardrails API and control the Workflow execution flow based on the returned results.

Step 1 - Add an HTTP Request Node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In the Dify Workflow orchestration interface, add a node and select the "HTTP Request" node from the tools. Configure the F5 Guardrails Scans API endpoint within the node.

..  image:: ./_static/integration-Dify-10.png

Step 2 - Use a JSON Processing Node to Handle the F5 Guardrails API Response
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add a "JSON Processing" node to the Workflow to handle the results returned from the F5 Guardrails API. Connect the output of the HTTP Request node to the input of the JSON Processing node.

..  image:: ./_static/integration-Dify-11.png

Based on the output of the JSON Processing node, you can add conditional branching nodes to control the Workflow execution flow — for example, if the result is flagged, execute a specific action.

Step 3 - Test and Verify the Workflow Execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In the Workflow orchestration interface, click "Test Run" to test the Workflow execution. Observe whether the HTTP Request node successfully called the F5 Guardrails API, whether the JSON Processing node correctly handled the returned results, and verify the final output.

..  image:: ./_static/integration-Dify-12.png

- Part 5 - Using the F5 Guardrails tool node in a Workflow to call the F5 Guardrails Scans endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dify Workflows provide a rich set of tool nodes that can be searched for and installed from the Plugin center. If F5 Guardrails provides a dedicated tool node, users can use it directly in a Workflow to call the F5 Guardrails Scans endpoint and scan input and output content. This approach is more convenient and efficient than using a generic HTTP Request node, because a dedicated tool node typically encapsulates the details of interacting with the F5 Guardrails API, allowing users to focus solely on how to use the node.

..  Note::

   A dedicated F5 Guardrails tool node will be made available in the Dify Marketplace in the future; it has not yet been developed.
