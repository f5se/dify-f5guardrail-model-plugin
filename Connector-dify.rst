Connector - Dify
----------------
在与Dify的集成中，有以下几种方式：

- Part 1 - 使用Dify Marketpalce中的F5 Guardrails 模型 plugin
- Part 2 - 使用Dify自身提供的OpenAI compatible 模型 plugin来调用F5 Guardrails的OpenAI compatible API
- Part 3 - 使用Dify的Moderation API接口，调用F5 Guardrails的Scans接口
- Part 4 - 在Workflow中使用“HTTP请求节点”，调用F5 Guardrails的Scans接口
- Part 5 - 在Workflow中使用F5 Guardrails工具节点，调用F5 Guardrails的Scans接口


Part 1 - 使用Dify Marketpalce中的F5 Guardrails 模型 plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

该方法通过直接安装Dify Marketplace中的F5 Guardrails模型插件来实现集成。用户安装插件后，可以直接配置F5 Guardrails中的相关Project/Provider信息。该插件将F5 Guardrails的Prompts接口封装成一个模型，使用户能够在Dify中直接调用F5 Guardrails的功能来扫描输入输出内容。因此，这是一种Inline模式。

Step 1 - 安装插件
^^^^^^^^^^^^^^^^
在Dify界面的右上角点击"Plugins"，在出现的界面中点击"Explore Marketplace"，在Marketplace中搜索"F5"，找到插件后点击安装。
..  image:: ./_static/integration-Dify-01.png

..  Note:: 

   该插件具体细节可访问 https://marketplace.dify.ai/plugin/f5/f5_guardrail

Step 2 - 配置插件
^^^^^^^^^^^^^^^^
安装完成后，点击右上角用户头像，选择"Settings"，在Settings界面中选择"Model Provider"，找到已安装的F5 Guardrails插件，点击"Add API Key"进入插件配置界面。根据界面提示进行配置：
..  image:: ./_static/integration-Dify-02.png

Step 3 - 使用插件
^^^^^^^^^^^^^^^^
配置完成后，即可在Dify的App编排界面直接选择F5 Guardrails的模型作为LLM Provider,类似如下图所示：
..  image:: ./_static/integration-Dify-03.png


Part 2 - 使用Dify自身提供的OpenAI compatible 模型 plugin来调用F5 Guardrails的OpenAI compatible API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

该方法通过Dify自身提供的OpenAI compatible模型插件来调用F5 Guardrails的OpenAI compatible API接口。用户需要在Dify中安装OpenAI compatible模型插件，并将其配置为指向F5 Guardrails的OpenAI compatible API端点。配置完成后，用户可以在Dify中直接使用这个新的模型插件来调用F5 Guardrails的功能。

.. Note:: 

   当F5 Guardrails出现blocking时，返回的API格式是非OpenAI的格式，因此需要部署一个透明代理来处理这些非OpenAI格式的响应，因此在下述Step 2步骤中填写的url实际是透明代理的url。
   透明代理服务程序可从这里获得:https://github.com/f5se/openai-f5-guardrail-api-converter

Step 1 - 安装插件
^^^^^^^^^^^^^^^^
在Dify界面的右上角点击"Plugins"，在出现的界面中点击"Explore Marketplace"，在Marketplace中搜索"OpenAI"，找到Dify自身提供的OpenAI compatible模型插件后点击安装。
..  image:: ./_static/integration-Dify-04.png

Step 2 - 配置插件
^^^^^^^^^^^^^^^^
在Dify界面的右上角点击"Settings"，在Settings界面中选择"Model Provider"，找到已安装的OpenAI compatible模型插件，点击"Add Model"进入插件配置界面。根据界面提示进行配置：
..  image:: ./_static/integration-Dify-05.png

Step 3 - 使用插件
^^^^^^^^^^^^^^^^
配置完成后，即可在Dify的App编排界面直接选择F5 Guardrails的模型作为LLM Provider,类似如下图所示：
..  image:: ./_static/integration-Dify-06.png

- Part 3 - 使用Dify的Moderation API接口，调用F5 Guardrails的Scans接口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

该方法通过Dify的Moderation API接口来调用F5 Guardrails的Scans接口。用户需要额外部署一个满足Dify Moderation API规范的服务接口，并在Dify的App中配置Moderation API。
Moderation API服务程序源码可以从这里获得 `Github repo <https://github.com/f5se/openai-f5-guardrail-api-converter>`_

Step 1 - 配置API Extension
^^^^^^^^^^^^^^^^^^^^^^^^^^
在Dify界面的右上角点击"Settings"，在Settings界面中选择"API Extension"，点击"Add API Extension"进入配置界面。根据界面提示进行配置：
..  image:: ./_static/integration-Dify-07.png

Step 2 - 配置Content moderation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
在具体的App中，一般为聊天类应用，在应用调试界面底部找到"Enable feature to enhance web app user experience",点击并启用"Content moderation", 在Moderation API的配置界面中，选择之前配置的API Extension，完成配置。
..  image:: ./_static/integration-Dify-08.png

Step 3 - 测试使用
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
应用直接选择未经过Guardrails的LLM，并进行对话测试，观察是否有敏感内容被正确识别和处理。
..  image:: ./_static/integration-Dify-09.png


- Part 4 - 在Workflow中使用“HTTP请求节点”，调用F5 Guardrails的Scans接口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在Workflow中，可以添加一个“HTTP请求节点”，并配置其请求URL为F5 Guardrails的Scans API，从而实现对输入输出内容的扫描。用户可以灵活的使用这个HTTP请求节点来调用F5 Guardrails的API，并根据返回的结果来控制Workflow的执行流程。

Step 1 - 添加HTTP请求节点
^^^^^^^^^^^^^^^^^^^^^^^
在Dify的Workflow编排界面，添加节点，并在工具中选择"HTTP Request"节点, 在节点中配置F5 Guardrails Scans API端点。
..  image:: ./_static/integration-Dify-10.png

Step 2 - 利用JSON处理节点，对F5 Guardrails的API响应进行处理
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
在Workflow中添加一个"JSON Processing"节点，用于处理从F5 Guardrails的API返回的结果。将HTTP请求节点的输出连接到JSON处理节点的输入。
..  image:: ./_static/integration-Dify-11.png

后续根据JSON处理节点的输出结果，可以添加条件判断节点来控制Workflow的执行流程，例如如果检测到结果是flagged，则执行特定的操作。

Step 3 - 测试验证Workflow运行结果
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
在Workflow编排界面，点击"Test Run"来测试Workflow的执行结果。观察HTTP请求节点是否成功调用了F5 Guardrails的API，并且JSON处理节点是否正确处理了返回的结果，以及最终输出。
..  image:: ./_static/integration-Dify-12.png

- Part 5 - 在Workflow中使用F5 Guardrails工具节点，调用F5 Guardrails的Scans接口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dify的Workflow中提供了丰富的工具节点，这些工具可以在Plugin中心进行搜索和安装。如果F5 Guardrails提供了专门的工具节点，那么用户可以直接在Workflow中使用这个工具节点来调用F5 Guardrails的Scans接口，从而实现对输入输出内容的扫描。这种方式比使用通用的HTTP请求节点更为便捷和高效，因为专门的工具节点通常会封装好与F5 Guardrails API交互的细节，用户只需要关注如何使用这个工具节点即可。

..  Note:: 

   后续将会在Dify的Marketplace中提供F5 Guardrails的工具节点, 目前暂未开发。
