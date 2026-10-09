发送包含文本和/或图像内容的结构化输入消息列表，模型将生成对话中的下一条消息。
统计 Message 中的 token 数量

POST
/v1/messages/count_tokens
统计 Message 中的 token 数量。
Models

Base64ImageSource
object
{
type
:
"base64"
,
data
,
media_type
}

type
:
"base64"

data
:
string

format
byte

media_type
:
"image/jpeg"
or
"image/png"
or
"image/gif"
or
"image/webp"

One of the following:
"image/jpeg"

"image/png"

"image/gif"

"image/webp"

Base64PDFSource
object
{
type
:
"base64"
,
data
,
media_type
}

type
:
"base64"

data
:
string

format
byte
media_type
:
"application/pdf"

BashCodeExecutionOutputBlock
object
{
type
:
"bash_code_execution_output"
,
file_id
}

type
:
"bash_code_execution_output"

default
bash_code_execution_output
file_id
:
string

BashCodeExecutionOutputBlockParam
object
{
type
:
"bash_code_execution_output"
,
file_id
}

type
:
"bash_code_execution_output"

file_id
:
string

BashCodeExecutionResultBlock
object
{
type
:
"bash_code_execution_result"
,
content
,
return_code
,
2
more
}

type
:
"bash_code_execution_result"

default
bash_code_execution_result

content
:
array of
BashCodeExecutionOutputBlock
{
type
:
"bash_code_execution_output"
,
file_id
}

type
:
"bash_code_execution_output"

default
bash_code_execution_output
file_id
:
string

return_code
:
number

stderr
:
string

stdout
:
string

BashCodeExecutionResultBlockParam
object
{
type
:
"bash_code_execution_result"
,
content
,
return_code
,
2
more
}

type
:
"bash_code_execution_result"

content
:
array of
BashCodeExecutionOutputBlockParam
{
type
:
"bash_code_execution_output"
,
file_id
}

type
:
"bash_code_execution_output"

file_id
:
string

return_code
:
number

stderr
:
string

stdout
:
string

BashCodeExecutionToolResultBlock
object
{
type
:
"bash_code_execution_tool_result"
,
content
,
tool_use_id
}

BashCodeExecutionToolResultBlockParam
object
{
type
:
"bash_code_execution_tool_result"
,
content
,
tool_use_id
,
cache_control
}

BashCodeExecutionToolResultError
object
{
type
:
"bash_code_execution_tool_result_error"
,
error_code
}

type
:
"bash_code_execution_tool_result_error"

default
bash_code_execution_tool_result_error

error_code
:
BashCodeExecutionToolResultErrorCode

下列之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

"output_file_too_large"

BashCodeExecutionToolResultErrorCode
=

"invalid_tool_input"
or
"unavailable"
or
"too_many_requests"
or
另外 2 个

下列之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

"output_file_too_large"

BashCodeExecutionToolResultErrorParam
object
{
type
:
"bash_code_execution_tool_result_error"
,
error_code
}

type
:
"bash_code_execution_tool_result_error"

error_code
:
BashCodeExecutionToolResultErrorCode

下列之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

"output_file_too_large"

BrowserClickTarget
=

BrowserCoordinateTarget
or
BrowserRefTarget

操作位置：视口坐标或元素引用。
下列之一：

BrowserCoordinateTarget
object
{
type
:
"coordinate"
,
x
,
y
}

浏览器视口中的一个点，以视口像素为单位（与全视口截图的坐标系相同）。
type
:
"coordinate"

x
:
number

距视口左边缘的像素数。
minimum
0

y
:
number

距视口上边缘的像素数。
minimum
0

BrowserRefTarget
object
{
type
:
"ref"
,
ref
}

页面上的一个元素，由先前
read_page
或
find
结果中的引用标识。引用作用域限于生成它的标签页，在导航或重大重新渲染后会失效。
type
:
"ref"

ref
:
string

由先前
read_page
或
find
结果返回的元素引用（例如 "ref_7"）。

BrowserCloseTabConfig
object
{
defer_loading
,
enabled
}

close_tab
' 的配置覆盖项。
defer_loading
:
optional
boolean
或
null

延迟加载此成员。必须在该 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
或
null

是否将此成员提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中隐去。

BrowserCloseTabInput
object
{
tab_id
}

关闭具有给定 tab_id 的标签页。
tab_id
:
string

要关闭的标签页。

BrowserCloseTabToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserCoordinateTarget
object
{
type
:
"coordinate"
,
x
,
y
}

浏览器视口中的一个点，以视口像素为单位（与 full-viewport screenshot 使用同一坐标系）。
type
:
"coordinate"


x
:
number

距视口左边缘的像素数。
minimum
0

y
:
number

距视口上边缘的像素数。
minimum
0

BrowserDoubleClickConfig
object
{
defer_loading
,
enabled
}

double_click
的配置覆盖项。
defer_loading
:
optional
boolean
或
null

延迟加载此成员。必须在该 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
或
null

是否将此成员提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中隐去。

BrowserDoubleClickInput
object
{
target
,
modifiers
,
tab_id
}

在视口坐标处或按引用在元素上双击左键。

BrowserDoubleClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserFileUploadConfig
object
{
defer_loading
,
enabled
}

file_upload
的配置覆盖项。
defer_loading
:
optional
boolean
或
null

延迟加载此成员。必须在该 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
或
null

此成员是否提供给模型。默认值因成员而异，具体参见工具集的文档。enabled 解析为 false 的成员会从提供的 schema 中移除。

BrowserFileUploadInput
object
{
target
,
document_ids
,
paths
,
tab_id
}

将一个 file-input 元素的值设置为一个或多个文件。target 必须是一个
元素引用；paths 或 document_ids 中至少有一个是必需的。

target
:
BrowserRefTarget
{
type
:
"ref"
,
ref
}

页面上的一个元素，由先前的
read_page
或
find
结果中的引用标识。引用作用域限于生成它们的标签页，并且在
导航或重大重新渲染后失效。
type
:
"ref"

ref
:
string

一个元素引用（例如 "ref_7"），由先前的
read_page
或
find
结果返回。

document_ids
:
optional
array of
string
or
null

指向 harness 已暂存文件的引用，用于浏览器执行器无法读取调用方文件系统的部署。
minItems
1

paths
:
optional
array of
string
or
null

浏览器执行器文件系统上的文件路径。
minItems
1
tab_id
:
optional
string
or
null

要操作的标签页。省略时默认为活动标签页。

BrowserFileUploadToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserFindConfig
object
{
defer_loading
,
enabled
}

find
的配置覆盖。
defer_loading
:
optional
boolean
or
null

为此成员延迟加载。必须在工具集的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值因成员而异，具体参见工具集的文档。enabled 解析为 false 的成员会从提供的 schema 中移除。

BrowserFindInput
object
{
query
,
tab_id
}

查找与自然语言描述匹配的元素（例如“搜索栏”、“添加到
购物车按钮”），并返回最多 20 个带有元素引用的匹配项。
query
:
string

要查找的元素的自然语言描述。
tab_id
:
optional
string
or
null

要操作的标签页。省略时默认为活动标签页。
BrowserFindToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserFormInputConfig
object
{
defer_loading
,
enabled
}
form_input 的 config 覆盖项。
defer_loading
:
optional
boolean
or
null
为此成员延迟加载。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null
是否将此成员提供给模型。默认值因成员而异，以 toolset 的文档为准。enabled 解析为 false 的成员会从提供的 schema 中隐去。
BrowserFormInputInput
object
{
target
,
value
,
tab_id
}
设置表单元素（input、textarea、select、checkbox）的值。对于 checkbox 使用 boolean，对于 select 使用选项值或文本。
target
:
BrowserRefTarget
{
type
:
"ref"
,
ref
}
页面上的元素，由先前的 read_page 或 find 结果中的引用标识。引用作用域限定于生成它们的标签页，并在导航或重大重新渲染后失效。
type
:
"ref"
ref
:
string
由先前的 read_page 或 find 结果返回的元素引用（例如 "ref_7"）。
value
:
BrowserFormInputValue
要设置的值。
以下之一：
string
number
boolean
tab_id
:
optional
string
or
null
要操作的标签页。省略时默认为活动标签页。
BrowserFormInputToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserFormInputValue
=

string
or
number
or
boolean
以下之一：
string
number
boolean
BrowserGetPageTextConfig
object
{
defer_loading
,
enabled
}
get_page_text 的 config 覆盖项。
defer_loading
:
optional
boolean
or
null
为此成员延迟加载。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null
是否将此成员提供给模型。默认值因成员而异，以 toolset 的文档为准。enabled 解析为 false 的成员会从提供的 schema 中隐去。
BrowserGetPageTextInput
object
{
tab_id
}
Return the page's visible text content as plain text, prioritizing article
content. Suited to articles, documentation, and other text-heavy pages.
tab_id
:
optional
string
or
null
Tab to act on. Defaults to the active tab when omitted.
BrowserGetPageTextToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserHoldKeyConfig
object
{
defer_loading
,
enabled
}
hold_key
's config overrides.
defer_loading
:
optional
boolean
or
null
为此成员延迟加载。必须在工具集中每个已启用的成员上解析为相同的值。
enabled
:
optional
boolean
or
null
是否将此成员提供给模型。默认值因成员而异，参见工具集的文档。enabled 解析为 false 的成员将从提供的 schema 中扣留。
BrowserHoldKeyInput
object
{
duration
,
text
,
tab_id
}
按住某个键或组合键一段时间，然后松开。使用与 key 操作相同的键名
和 "+" 组合键语法。
duration
:
number
按住该键的秒数（最大 30）。
minimum
0
maximum
30
text
:
string
要按住的键或组合键。
tab_id
:
optional
string
or
null
要操作的 Tab。省略时默认为当前活动 Tab。
BrowserHoldKeyToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserHoverConfig
object
{
defer_loading
,
enabled
}
hover
's config overrides.
defer_loading
:
optional
boolean
or
null
为此成员延迟加载。必须在工具集中每个已启用的成员上解析为相同的值。
enabled
:
optional
boolean
or
null
是否将此成员提供给模型。默认值因成员而异，参见工具集的文档。enabled 解析为 false 的成员将从提供的 schema 中扣留。
BrowserHoverInput
object
{
target
,
tab_id
}
将光标移动到某个坐标或元素上，而不点击。
BrowserHoverToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserJavascriptExecConfig
object
{
defer_loading
,
enabled
}

javascript_exec
的配置覆盖项。
defer_loading
：
可选
boolean
或
null

为此成员延迟加载。必须在 toolset 的每个已启用成员上解析为相同的值。
enabled
：
可选
boolean
或
null

是否向模型提供此成员。默认值按成员决定，依据 toolset 的文档。如果某个成员的 enabled 解析为 false，则该成员会从提供的 schema 中隐去。

BrowserJavascriptExecInput
object
{
text
,
tab_id
}

在页面上下文中执行 JavaScript，并返回最后一个表达式的值。代码运行时可以访问 DOM、
window
以及页面变量。
编写你想要被求值的表达式——不要使用
return
。
text
：
string

要在页面上下文中执行的 JavaScript。
tab_id
：
可选
string
或
null

要操作的标签页。省略时默认为活动标签页。

BrowserJavascriptExecToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserKeyConfig
object
{
defer_loading
,
enabled
}

key
的配置覆盖项。
defer_loading
：
可选
boolean
或
null

为此成员延迟加载。必须在 toolset 的每个已启用成员上解析为相同的值。
enabled
：
可选
boolean
或
null

是否向模型提供此成员。默认值按成员决定，依据 toolset 的文档。如果某个成员的 enabled 解析为 false，则该成员会从提供的 schema 中隐去。

BrowserKeyInput
object
{
text
,
repeat
,
tab_id
}

按下一个键或按键组合。使用“+”将修饰键与某个键组合（例如“ctrl+a”、“cmd+shift+p”），并使用空格来编排连续按键（例如“Backspace Backspace Delete”）。
支持“Return”、“Tab”、“Escape”、“BackSpace”等常见名称。
text
：
string

要按下的键、按键组合，或以空格分隔的按键序列。

repeat
：
可选
number
或
null

重复次数。默认 1。
minimum
1
maximum
100
tab_id
：
可选
string
或
null

要操作的标签页。省略时默认为活动标签页。

BrowserKeyToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserLeftClickConfig
object
{
defer_loading
,
enabled
}

left_click
的配置覆盖项。
defer_loading
:
optional
boolean
or
null

为此成员延迟加载。必须在该 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，依据 toolset 的文档。enabled 解析为 false 的成员会从 served schema 中排除。

BrowserLeftClickDragConfig
object
{
defer_loading
,
enabled
}

left_click_drag
的配置覆盖项。
defer_loading
:
optional
boolean
or
null

为此成员延迟加载。必须在该 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，依据 toolset 的文档。enabled 解析为 false 的成员会从 served schema 中排除。

BrowserLeftClickDragInput
object
{
from
,
target
,
tab_id
}

在
from
处按下，拖拽到
target
，释放。两者都必须是 coordinate targets。

BrowserLeftClickDragToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserLeftClickInput
object
{
target
,
modifiers
,
tab_id
}

在 viewport 坐标处左键单击，或按引用在 element 上左键单击。

BrowserLeftClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserLeftMouseDownConfig
object
{
defer_loading
,
enabled
}

left_mouse_down
的配置覆盖项。
defer_loading
:
optional
boolean
or
null

为此成员延迟加载。必须在该 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，依据 toolset 的文档。enabled 解析为 false 的成员会从 served schema 中排除。

BrowserLeftMouseDownInput
object
{
target
,
tab_id
}

在 viewport 坐标处按住鼠标左键。与
left_mouse_up 搭配以执行自定义拖拽。

target
:
BrowserCoordinateTarget
{
type
:
"coordinate"
,
x
,
y
}

浏览器 viewport 中的一个点，以 viewport 像素为单位（与全 viewport 截图相同的坐标系）。
type
:
"coordinate"


x
:
number

距 viewport 左边缘的像素数。
minimum
0

y
:
number

距 viewport 上边缘的像素数。
minimum
0
tab_id
:
optional
string
or
null

要操作的 tab。省略时默认为活动 tab。

BrowserLeftMouseDownToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserLeftMouseUpConfig
object
{
defer_loading
,
enabled
}

left_mouse_up
的 config 覆盖项。
defer_loading
:
optional
boolean
or
null

此成员的延迟加载。必须在 toolset 的每个已启用成员上解析为相同的值。
enabled
:
optional
boolean
or
null

是否向模型提供此成员。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中移除。

BrowserLeftMouseUpInput
object
{
target
,
tab_id
}

在 viewport 坐标处释放鼠标左键。

target
:
BrowserCoordinateTarget
{
type
:
"coordinate"
,
x
,
y
}

浏览器 viewport 中的一个点，以 viewport 像素为单位（与全 viewport 截图相同的坐标系）。
type
:
"coordinate"


x
:
number

距 viewport 左边缘的像素数。
minimum
0

y
:
number

距 viewport 上边缘的像素数。
minimum
0
tab_id
:
optional
string
or
null

要操作的 tab。省略时默认为活动 tab。

BrowserLeftMouseUpToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserListTabsConfig
object
{
defer_loading
,
enabled
}

list_tabs
的 config 覆盖项。
defer_loading
:
optional
boolean
or
null

此成员的延迟加载。必须在 toolset 的每个已启用成员上解析为相同的值。
enabled
:
optional
boolean
or
null

是否向模型提供此成员。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中移除。
BrowserListTabsInput
object
{
}
列出所有打开的 tab，包含每个 tab 的 tab_id、title 和 URL。
BrowserListTabsToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserMiddleClickConfig
object
{
defer_loading
,
enabled
}
middle_click
的 config 覆盖项。
defer_loading
:
optional
boolean
or
null
延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null
是否将此成员提供给 model。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员不会出现在所提供（served）的 schema 中。
BrowserMiddleClickInput
object
{
target
,
modifiers
,
tab_id
}
在 viewport 坐标处或按引用在元素上执行中键点击。
BrowserMiddleClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserMouseMoveConfig
object
{
defer_loading
,
enabled
}
mouse_move
的 config 覆盖项。
defer_loading
:
optional
boolean
or
null
延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null
是否将此成员提供给 model。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员不会出现在所提供（served）的 schema 中。
BrowserMouseMoveInput
object
{
target
,
tab_id
}
将指针移动到某个 viewport 坐标，不进行点击。
target
:
BrowserCoordinateTarget
{
type
:
"coordinate"
,
x
,
y
}
浏览器 viewport 中的一个点，以 viewport 像素为单位（与
full-viewport screenshot 同一坐标系）。
type
:
"coordinate"
x
:
number
距 viewport 左边缘的像素数。
minimum
0
y
:
number
距 viewport 上边缘的像素数。
minimum
0
tab_id
:
optional
string
or
null
要操作的 tab。省略时默认为活动 tab。
BrowserMouseMoveToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
BrowserNavigateConfig
object
{
defer_loading
,
enabled
}
navigate
的配置覆盖项。
defer_loading
：
可选
boolean
或
null

延迟加载此成员。必须在工具集中每个已启用的成员上解析为相同的值。
enabled
：
可选
boolean
或
null

此成员是否提供给模型。默认值因成员而异，参见工具集的文档。enabled 解析为 false 的成员会从所提供的 schema 中移除。

BrowserNavigateInput
object
{
url
,
tab_id
}

导航到某个 URL，或在历史记录中后退/前进/重新加载。协议可以
省略（默认为 https://）。
url
：
string

要导航到的 URL，或用于历史导航的 "back" / "forward" / "reload"。
tab_id
：
可选
string
或
null

要操作的标签页。省略时默认为活动标签页。

BrowserNavigateToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

BrowserNewTabConfig
object
{
defer_loading
,
enabled
}

new_tab
的配置覆盖项。
defer_loading
：
可选
boolean
或
null

延迟加载此成员。必须在工具集中每个已启用的成员上解析为相同的值。
enabled
：
可选
boolean
或
null

此成员是否提供给模型。默认值因成员而异，参见工具集的文档。enabled 解析为 false 的成员会从所提供的 schema 中移除。

BrowserNewTabInput
object
{
}

打开一个新的空标签页并返回其 tab_id。

BrowserNewTabToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

BrowserReadConsoleConfig
object
{
defer_loading
,
enabled
}

read_console
的配置覆盖项。
defer_loading
：
可选
boolean
或
null

延迟加载此成员。必须在工具集中每个已启用的成员上解析为相同的值。
enabled
：
可选
boolean
或
null

此成员是否提供给模型。默认值因成员而异，参见工具集的文档。enabled 解析为 false 的成员会从所提供的 schema 中移除。

BrowserReadConsoleInput
object
{
tab_id
}

返回自……以来累积的 console 输出（日志条目、错误、警告）。
driver 附加到 tab 之后以及自上次读取以来，每个条目一行。空结果并不意味着对于在 attach 之前就已存在的 tab 没有流量。
tab_id
:
optional
string
或
null

要操作的 tab。省略时默认为活动 tab。

BrowserReadConsoleToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
另有 3 项
}

BrowserReadNetworkConfig
object
{
defer_loading
,
enabled
}

read_network 的 config 覆盖项。
defer_loading
:
optional
boolean
或
null

此成员的延迟加载。在 toolset 的每个已启用成员上，必须解析为相同的值。
enabled
:
optional
boolean
或
null

此成员是否提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中隐去。

BrowserReadNetworkInput
object
{
tab_id
}

返回自 driver 附加到 tab 以来以及自上次读取以来记录的 network 请求（method、URL、状态、MIME type、timing），每个条目一行。空结果并不意味着对于在 attach 之前就已存在的 tab 没有流量。
tab_id
:
optional
string
或
null

要操作的 tab。省略时默认为活动 tab。

BrowserReadNetworkToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
另有 3 项
}

BrowserReadPageConfig
object
{
defer_loading
,
enabled
}

read_page 的 config 覆盖项。
defer_loading
:
optional
boolean
或
null

此成员的延迟加载。在 toolset 的每个已启用成员上，必须解析为相同的值。
enabled
:
optional
boolean
或
null

此成员是否提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中隐去。

BrowserReadPageFilter
=

"all"
或
"interactive"

以下之一：
"all"

"interactive"

BrowserReadPageInput
object
{
depth
,
filter
,
ref
,
tab_id
}

返回页面的结构化 accessibility tree（或以
ref 为根的子树
），带有类似 [ref_7] 的元素引用，可在后续
操作中用作目标。输出上限为 50,000 个字符 — 超出时使用
ref
或更小的
depth
来缩小范围。

depth
:
可选
number
或
null

最大树深度。默认 15。
最小值
1

filter
:
可选
BrowserReadPageFilter
或
null

要包含哪些元素。省略时：每个可见元素。"interactive"：仅交互式元素。"all"：额外包含视口外元素。
以下之一：
"all"

"interactive"

ref
:
可选
string
或
null

从中读取子树的元素引用。省略则从页面根读取。
tab_id
:
可选
string
或
null

要操作的标签页。省略时默认为活动标签页。

BrowserReadPageToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserRefTarget
object
{
type
:
"ref"
,
ref
}

页面上的一个元素，由先前的
read_page
或
find
结果中的引用标识。引用作用于生成它们的标签页，并在
导航或主要重新渲染后失效。
type
:
"ref"

ref
:
string

由先前的
read_page
或
find
结果返回的元素引用（例如 "ref_7"）。

BrowserRightClickConfig
object
{
defer_loading
,
enabled
}

right_click
的配置覆盖。
defer_loading
:
可选
boolean
或
null

为此成员延迟加载。必须在 toolset 的每个已启用成员上解析为相同的值。
enabled
:
可选
boolean
或
null

此成员是否提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员将从提供的 schema 中扣留。

BrowserRightClickInput
object
{
target
,
modifiers
,
tab_id
}

在 viewport 坐标处或按引用在元素上右键单击。

BrowserRightClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserScreenshotConfig
object
{
defer_loading
,
enabled
}

screenshot
的配置覆盖。
defer_loading
:
可选
boolean
或
null

延迟此 member 的加载。必须在 toolset 的每个 enabled member 上解析为相同的值。
enabled
:
optional
boolean
or
null

此 member 是否提供给 model。默认值因 member 而异，具体见 toolset 的文档。enabled 解析为 false 的 member 会从所提供的 schema 中扣留。

BrowserScreenshotInput
object
{
tab_id
}

捕获当前浏览器视口。
tab_id
:
optional
string
or
null

要操作的 tab。省略时默认为活动 tab。

BrowserScreenshotToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserScrollConfig
object
{
defer_loading
,
enabled
}

scroll
的配置覆盖。
defer_loading
:
optional
boolean
or
null

延迟此 member 的加载。必须在 toolset 的每个 enabled member 上解析为相同的值。
enabled
:
optional
boolean
or
null

此 member 是否提供给 model。默认值因 member 而异，具体见 toolset 的文档。enabled 解析为 false 的 member 会从所提供的 schema 中扣留。

BrowserScrollDirection
=

"up"
or
"down"
or
"left"
or
"right"

以下之一：
"up"

"down"

"left"

"right"


BrowserScrollInput
object
{
scroll_direction
,
target
,
scroll_amount
,
tab_id
}

在视口位置滚动。
target
必须是坐标 target。

scroll_direction
:
BrowserScrollDirection

以下之一：
"up"

"down"

"left"

"right"


target
:
BrowserCoordinateTarget
{
type
:
"coordinate"
,
x
,
y
}

浏览器视口中的一个点，以视口像素为单位（与
full-viewport screenshot 相同的帧）。
type
:
"coordinate"


x
:
number

从视口左边缘算起的像素数。
minimum
0

y
:
number

从视口上边缘算起的像素数。
minimum
0

scroll_amount
:
optional
number
or
null

滚轮槽口数（1–10）。默认 3。
minimum
1
maximum
10
tab_id
:
optional
string
or
null

要操作的 tab。省略时默认为活动 tab。

BrowserScrollToConfig
object
{
defer_loading
,
enabled
}

scroll_to
的配置覆盖项。
defer_loading
：
optional
boolean
或
null

延迟加载此成员。必须在工具集的每个启用成员上解析为相同的值。
enabled
：
optional
boolean
或
null

此成员是否提供给模型。默认值按成员而定，参见工具集的文档。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

BrowserScrollToInput
object
{
target
,
tab_id
}

将元素滚动到视图中。

target
：
BrowserRefTarget
{
type
：
"ref"
,
ref
}

页面上的一个元素，由先前
read_page
或
find
结果中的引用标识。引用的作用域限定为产生它们的标签页，并且在导航或重大重新渲染后
变为失效。
type
：
"ref"

ref
：
string

由先前
read_page
或
find
结果返回的元素引用（例如 "ref_7"）。
tab_id
：
optional
string
或
null

要操作的标签页。省略时默认为活动标签页。

BrowserScrollToToolUseBlock
object
{
type
：
"tool_use"
,
id
,
caller
,
3
more
}


BrowserScrollToolUseBlock
object
{
type
：
"tool_use"
,
id
,
caller
,
3
more
}


BrowserStateBlockParam
object
{
type
：
"browser_state"
,
tabs
,
cache_control
,
state_changes
}

调用方的浏览器状态，在一次浏览器工具集成员调用之后——
打开标签页的完整清单、哪个标签页处于活动状态，以及该调用产生的任何副作用
（打开的标签页、下载状态变化）。
每个
tool_result
至多一个，且仅出现在应答
浏览器工具集成员
tool_use
的非错误结果上。服务器从它渲染出
模型可见的文本；模型永远看不到原始字段。

BrowserStateChange
=

BrowserStateChangeTabOpened
或
BrowserStateChangeDownloadStarted
或
BrowserStateChangeDownloadCompleted
或
BrowserStateChangeDownloadFailed

以下之一：

BrowserStateChangeDownloadCompleted
object
{
type
：
"download_completed"
,
download_id
,
url
,
2
more
}

在此次调用期间完成的文件下载，报告时使用与其
download_started
相同的
download_id
——或者在没有先前
download_started
，当下载在启动它的调用期间完成时（每个
download_id
每个结果至多一次状态变更）。
type
:
"download_completed"


download_id
:
string

调用方为此下载分配的标识符，在报告它的各次状态变更之间保持稳定。
minLength
1
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

url
:
string

下载最终由哪个重定向后的 URL 提供。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

path
:
optional
string
or
null

executor 在 executor 的文件系统上保存文件的位置。仅当同一环境中的另一个 tool 能在该路径读取文件时才包含。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

size_bytes
:
optional
number
or
null

已完成下载的大小。
minimum
0

BrowserStateChangeDownloadFailed
object
{
type
:
"download_failed"
,
download_id
,
url
,
error
}

在此次调用期间失败——或被取消——的文件下载。
type
:
"download_failed"


download_id
:
string

调用方为此下载分配的标识符，在报告它的各次状态变更之间保持稳定。
minLength
1
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

url
:
string

下载最终由哪个重定向后的 URL 提供。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

error
:
optional
string
or
null

失败或取消的详细信息（如果已知）。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

BrowserStateChangeDownloadStarted
object
{
type
:
"download_started"
,
download_id
,
url
}

在此次调用期间开始的文件下载。
type
:
"download_started"


download_id
:
string

调用方为此下载分配的标识符，在报告它的各次状态变更之间保持稳定。
minLength
1
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

url
:
string

下载最终由哪个重定向后的 URL 提供。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

BrowserStateChangeTabOpened
object
{
type
:
"tab_opened"
,
tab_id
}

此次调用执行期间打开、并在其结束时仍保持打开的一个标签页——
是
tabs
清单的创建增量，而非事件日志。
仅携带
tab_id
；该标签页的
title
和
url
存在于其
tabs
条目上，该条目必须包含相同的
tab_id
。在失败的调用期间打开的标签页不会获得延迟的
tab_opened
；它只会出现在下一个结果的
tabs
清单中。
type
:
"tab_opened"


tab_id
:
string

被打开标签页的
tab_id
，存在于
tabs
中。
minLength
1
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

BrowserStateTabEntry
object
{
tab_id
,
title
,
url
,
active
}

在
browser_state
块的
tabs
清单中报告的一个打开的浏览器标签页。
tab_id
是调用方为该标签页分配的标识符；
title
和
url
描述该标签页当前显示的页面，可能为空
字符串（空白标签页两者合法地均为空）。
active
标记此次调用后处于活动状态的
标签页；只要
tabs
非空，
恰好有一个条目被标记。

tab_id
:
string

此标签页的调用方分配标识符，在清单中唯一。
minLength
1
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

title
:
string

该标签页所示页面的标题。可能为空。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$

url
:
string

该标签页所示页面的 URL。可能为空。
maxLength
4096
pattern
^[^\x00-\x1f\x7f-\x9f\u2028\u2029]_$
active
:
optional
boolean

此标签页在此次调用后是否为活动标签页。只要
tabs
非空，
恰好有一个条目被标记为
active: true
。

BrowserSwitchTabConfig
object
{
defer_loading
,
enabled
}

switch_tab
的配置覆盖项。
defer_loading
:
optional
boolean
or
null

为此成员延迟加载。必须在工具集的每个已启用成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值按成员而定，参见该 toolset 的文档。enabled 解析为 false 的成员会从所服务的 schema 中撤回。

BrowserSwitchTabInput
object
{
tab_id
}

将具有给定 tab_id 的 tab 设为活动 tab —— 即不带 tab_id 的 action 所作用于的 tab。
tab_id
:
string

要切换到的 tab。

BrowserSwitchTabToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

BrowserToolUseBlock
=

BrowserNavigateToolUseBlock
or
BrowserListTabsToolUseBlock
or
BrowserNewTabToolUseBlock
or
28
more

以下之一：

BrowserToolset20260801
object
{
type
:
"browser_toolset_20260801"
,
cache_control
,
configs
}

browser toolset：单个
tools[]
条目（不携带
name
），用于声明 browser 工具族。模型所获得的是该族的工具，其中通过
configs
禁用的任何成员都会从其 schema 中移除。

BrowserToolsetConfigs
object
{
type
,
close_tab
,
double_click
,
28
more
}

browser_toolset_20260801
的逐成员配置：每个成员工具对应一个可选字段，以成员名作为键 —— 即该成员的
tool_use
块所携带的同一个名称。每个成员都是可接受的键，某成员的键缺失处即应用其默认值。未知键会被拒绝：该字段集就是此 toolset 版本的完整成员集。

BrowserTripleClickConfig
object
{
defer_loading
,
enabled
}

triple_click
的配置覆盖项。
defer_loading
:
optional
boolean
or
null

该成员的延迟加载（defer loading）。在该 toolset 每个已启用的成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值按成员而定，参见该 toolset 的文档。enabled 解析为 false 的成员会从所服务的 schema 中撤回。

BrowserTripleClickInput
object
{
target
,
modifiers
,
tab_id
}

在 viewport 坐标处或按引用对元素三击左键
（通常用于选中一行或一段）。

BrowserTripleClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserTypeConfig
object
{
defer_loading
,
enabled
}

type 的配置覆盖。
defer_loading
:
optional
boolean
or
null

此成员的延迟加载。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，具体依据 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

BrowserTypeInput
object
{
text
,
tab_id
}

在当前焦点处键入字面字符串。
text
:
string

要键入的文本。
tab_id
:
optional
string
or
null

要操作的 tab。省略时默认为活动 tab。

BrowserTypeToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserWaitConfig
object
{
defer_loading
,
enabled
}

wait 的配置覆盖。
defer_loading
:
optional
boolean
or
null

此成员的延迟加载。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，具体依据 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

BrowserWaitInput
object
{
duration
,
tab_id
}

暂停给定的 duration。

duration
:
number

等待的秒数（最大 30）。
minimum
0
maximum
30
tab_id
:
optional
string
or
null

要操作的 tab。省略时默认为活动 tab。

BrowserWaitToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


BrowserZoomConfig
object
{
defer_loading
,
enabled
}

zoom 的配置覆盖。
defer_loading
:
optional
boolean
or
null

此成员的延迟加载。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，具体依据 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

BrowserZoomInput
object
{
region
,
tab_id
}

返回给定视口区域的裁剪截图，放大以便更仔细地查看——对于小图标、按钮或文本很有用。坐标与完整截图处于相同的视口像素空间。

region
:
number 数组

[x0, y0, x1, y1] 以视口像素为单位。
minItems
4
maxItems
4
tab_id
:
optional
string
或
null

要操作的 Tab。省略时默认为活动 Tab。

BrowserZoomToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
另外 3 个
}

CacheControlEphemeral
object
{
type
:
"ephemeral"
,
ttl
}

type
:
"ephemeral"

ttl
:
optional
"5m"
或
"1h"

缓存控制断点的 time-to-live。
可以是以下值之一：
5m
: 5 分钟
1h
: 1 小时
默认为
5m
。有关详细信息，请参阅
prompt caching pricing
。
以下之一：
"5m"

"1h"

CacheCreation
object
{
ephemeral_1h_input_tokens
,
ephemeral_5m_input_tokens
}

ephemeral_1h_input_tokens
:
number

用于创建 1 小时缓存条目的输入 token 数量。
default
0
minimum
0

ephemeral_5m_input_tokens
:
number

用于创建 5 分钟缓存条目的输入 token 数量。
default
0
minimum
0

CacheMissMessagesChanged
object
{
type
:
"messages_changed"
,
cache_missed_input_tokens
}

type
:
"messages_changed"

default
messages_changed
cache_missed_input_tokens
:
number

如果前缀与先前的请求匹配，本应从缓存中读取的输入 token 的近似数量。

CacheMissModelChanged
object
{
type
:
"model_changed"
,
cache_missed_input_tokens
}

type
:
"model_changed"

default
model_changed
cache_missed_input_tokens
:
number

如果前缀与先前的请求匹配，本应从缓存中读取的输入 token 的近似数量。

CacheMissPreviousMessageNotFound
object
{
type
:
"previous_message_not_found"
}

type
:
"previous_message_not_found"

default
previous_message_not_found

CacheMissReason
=

CacheMissModelChanged
或
CacheMissSystemChanged
或
CacheMissToolsChanged
或
3
更多
下列之一：
CacheMissSystemChanged
object
{
type
:
"system_changed"
,
cache_missed_input_tokens
}
type
:
"system_changed"
default
system_changed
cache_missed_input_tokens
:
number
如果前缀与之前的请求匹配，本应从 cache 中读取的 input token 的近似数量。
CacheMissToolsChanged
object
{
type
:
"tools_changed"
,
cache_missed_input_tokens
}
type
:
"tools_changed"
default
tools_changed
cache_missed_input_tokens
:
number
如果前缀与之前的请求匹配，本应从 cache 中读取的 input token 的近似数量。
CacheMissUnavailable
object
{
type
:
"unavailable"
}
type
:
"unavailable"
default
unavailable
CitationCharLocation
object
{
type
:
"char_location"
,
cited_text
,
document_index
,
4
更多
}
type
:
"char_location"
default
char_location
cited_text
:
string
document_index
:
number
minimum
0
document_title
:
string
或
null
end_char_index
:
number
file_id
:
string
或
null
start_char_index
:
number
minimum
0
CitationCharLocationParam
object
{
type
:
"char_location"
,
cited_text
,
document_index
,
3
更多
}
type
:
"char_location"
cited_text
:
string
document_index
:
number
minimum
0
document_title
:
string
或
null
minLength
1
maxLength
500
end_char_index
:
number
start_char_index
:
number
minimum
0
CitationContentBlockLocation
object
{
type
:
"content_block_location"
,
cited_text
,
document_index
,
4
更多
}
type
:
"content_block_location"
default
content_block_location
cited_text
:
string
所引用 block 范围的完整文本，已拼接。
始终等于
content[start_block_index:end_block_index]
连接后的内容。该文本 block 是最小可引用单元；此字段绝不会是单个 block 的子字符串。不计入 output token，在后续轮次中回传时也不计入 input token。
document_index
:
number
minimum
0
document_title
:
string 或 null

end_block_index: number
source 的 content 数组中所引用 block 范围的 exclusive 0-based end index。始终大于 start_block_index；单 block 引用的 end_block_index = start_block_index + 1。

file_id: string 或 null

start_block_index: number
source 的 content 数组中第一个被引用 block 的 0-based index。

minimum 0

CitationContentBlockLocationParam object { type: "content_block_location", cited_text, document_index, 另有 3 项 }

type: "content_block_location"

cited_text: string
所引用 block 范围的完整文本，已拼接。始终等于 content[start_block_index:end_block_index] 的内容连接在一起。text block 是最小可引用单元；此字段绝不会是单个 block 的子字符串。不计入 output tokens；并且在后续轮次中回传时不计入 input tokens。

document_index: number

minimum 0

document_title: string 或 null

minLength 1
maxLength 500

end_block_index: number
source 的 content 数组中所引用 block 范围的 exclusive 0-based end index。始终大于 start_block_index；单 block 引用的 end_block_index = start_block_index + 1。

start_block_index: number
source 的 content 数组中第一个被引用 block 的 0-based index。

minimum 0

CitationPageLocation object { type: "page_location", cited_text, document_index, 另有 4 项 }

type: "page_location"
default page_location

cited_text: string

document_index: number

minimum 0

document_title: string 或 null

end_page_number: number

file_id: string 或 null

start_page_number: number

minimum 1

CitationPageLocationParam object { type: "page_location", cited_text, document_index, 另有 3 项 }

type: "page_location"

cited_text: string

document_index: number

minimum 0

document_title: string 或 null

minLength 1
maxLength 500

end_page_number: number

start_page_number: number

minimum 1
CitationSearchResultLocationParam
object
{
type
:
"search_result_location"
,
cited_text
,
end_block_index
,
4
more
}

type
:
"search_result_location"

cited_text
:
string

被引用块范围的完整文本，已拼接。始终等于 content[start_block_index:end_block_index] 的内容连接在一起后的结果。文本块是最小的可引用单元；该字段永远不会是单个块的子字符串。不计入输出 token，在后续轮次中回传时也不计入输入 token。

end_block_index
:
number

所引用块范围在源的 content 数组中基于 0 的排他性结束索引。始终大于 start_block_index；单块引用的 end_block_index = start_block_index + 1。

search_result_index
:
number

所引用搜索结果在请求中所有 search_result 内容块之间的基于 0 的索引，按它们在消息和工具结果中出现的顺序排列。与 document_index 分开计数；服务端 web search 结果不计入此计数。

minimum
0

source
:
string

start_block_index
:
number

源 content 数组中第一个被引用块的基于 0 的索引。

minimum
0

title
:
string
or
null

CitationWebSearchResultLocationParam
object
{
type
:
"web_search_result_location"
,
cited_text
,
encrypted_index
,
2
more
}

type
:
"web_search_result_location"

cited_text
:
string

encrypted_index
:
string

title
:
string
or
null

minLength
1

maxLength
512

url
:
string

minLength
1

CitationsConfig
object
{
enabled
}

enabled
:
boolean

default
false

CitationsConfigParam
object
{
enabled
}

enabled
:
optional
boolean

CitationsDelta
object
{
type
:
"citations_delta"
,
citation
}

CitationsSearchResultLocation
object
{
type
:
"search_result_location"
,
cited_text
,
end_block_index
,
4
more
}

type
:
"search_result_location"

default
search_result_location

cited_text
:
string

被引用块范围的完整文本，已拼接。
始终等于 `content[start_block_index:end_block_index]` 拼接后的内容。text block 是最小的可引用单元；该字段永远不会是单个 block 的子串。不计入 output token，在后续轮次回传时也不计入 input token。

end_block_index
:
number

source 的 `content` 数组中，被引用 block 范围的排除式 0 基结束索引。

始终大于 `start_block_index`；单 block 引用时 `end_block_index = start_block_index + 1`。

search_result_index
:
number

被引用的 search result 在请求中所有 `search_result` content block 中的 0 基索引，按其在各 message 与 tool result 中出现的顺序排列。

与 `document_index` 分开计数；服务端 web search 结果不计入此计数。

minimum
0

source
:
string

start_block_index
:
number

source 的 `content` 数组中第一个被引用 block 的 0 基索引。

minimum
0

title
:
string
或
null

CitationsWebSearchResultLocation
object
{
type
:
"web_search_result_location"
,
cited_text
,
encrypted_index
,
另外 2 项
}

type
:
"web_search_result_location"

default
web_search_result_location

cited_text
:
string

encrypted_index
:
string

title
:
string
或
null

maxLength
512

url
:
string

CodeExecutionOutputBlock
object
{
type
:
"code_execution_output"
,
file_id
}

type
:
"code_execution_output"

default
code_execution_output

file_id
:
string

CodeExecutionOutputBlockParam
object
{
type
:
"code_execution_output"
,
file_id
}

type
:
"code_execution_output"

file_id
:
string

CodeExecutionResultBlock
object
{
type
:
"code_execution_result"
,
content
,
return_code
,
另外 2 项
}

type
:
"code_execution_result"

default
code_execution_result

content
:
CodeExecutionOutputBlock
的数组
{
type
:
"code_execution_output"
,
file_id
}

type
:
"code_execution_output"

default
code_execution_output

file_id
:
string

return_code
:
number

stderr
:
string

stdout
:
string
CodeExecutionResultBlockParam
object
{
type
:
"code_execution_result"
,
content
,
return_code
,
2
更多
}

type
:
"code_execution_result"


content
:
array of
CodeExecutionOutputBlockParam
{
type
:
"code_execution_output"
,
file_id
}

type
:
"code_execution_output"

file_id
:
string

return_code
:
number

stderr
:
string

stdout
:
string


CodeExecutionTool20250522
object
{
type
:
"code_execution_20250522"
,
name
,
allowed_callers
,
3
更多
}


CodeExecutionTool20250825
object
{
type
:
"code_execution_20250825"
,
name
,
allowed_callers
,
3
更多
}


CodeExecutionTool20260120
object
{
type
:
"code_execution_20260120"
,
name
,
allowed_callers
,
3
更多
}

具有 REPL 状态持久化的代码执行工具（daemon 模式 + gVisor checkpoint）。

CodeExecutionTool20260521
object
{
type
:
"code_execution_20260521"
,
name
,
allowed_callers
,
3
更多
}

具有 REPL 状态持久化的代码执行工具。

CodeExecutionToolResultBlock
object
{
type
:
"code_execution_tool_result"
,
content
,
tool_use_id
}


type
:
"code_execution_tool_result"

default
code_execution_tool_result

content
:
CodeExecutionToolResultBlockContent

以下之一：

tool_use_id
:
string

pattern
^srvtoolu_[a-zA-Z0-9_]+$

CodeExecutionToolResultBlockContent
=

CodeExecutionToolResultError
或
CodeExecutionResultBlock
或
EncryptedCodeExecutionResultBlock

以下之一：

CodeExecutionToolResultBlockParam
object
{
type
:
"code_execution_tool_result"
,
content
,
tool_use_id
,
cache_control
}

type
:
"code_execution_tool_result"


content
:
CodeExecutionToolResultBlockParamContent

以下之一：

tool_use_id
:
string

pattern
^srvtoolu_[a-zA-Z0-9_]+$

cache_control
:
optional
CacheControlEphemeral
{
type
:
"ephemeral"
,
ttl
}
或
null

在此内容块创建缓存控制断点。
type
:
"ephemeral"


ttl
:
optional
"5m"
或
"1h"

缓存控制断点的存活时间。
这可能是以下值之一：
5m
: 5 分钟
1h
: 1 小时
默认为
5m
。详见
prompt caching pricing
。

以下之一：
"5m"

"1h"

CodeExecutionToolResultBlockParamContent
=

CodeExecutionToolResultErrorParam
或
CodeExecutionResultBlockParam
或
EncryptedCodeExecutionResultBlockParam

以下之一：

CodeExecutionToolResultError
object
{
type
:
"code_execution_tool_result_error"
,
error_code
}

type
:
"code_execution_tool_result_error"

default
code_execution_tool_result_error

error_code
:
CodeExecutionToolResultErrorCode

以下之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

CodeExecutionToolResultErrorCode
=

"invalid_tool_input"
或
"unavailable"
或
"too_many_requests"
或
"execution_time_exceeded"

以下之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

CodeExecutionToolResultErrorParam
object
{
type
:
"code_execution_tool_result_error"
,
error_code
}

type
:
"code_execution_tool_result_error"

error_code
:
CodeExecutionToolResultErrorCode

以下之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

ComputerCursorPositionConfig
object
{
defer_loading
,
enabled
}

cursor_position
的 config 覆盖项。

defer_loading
:
optional
boolean
或
null

为此成员延迟加载。在 toolset 的每个已启用成员上必须解析为相同的值。

enabled
:
optional
boolean
或
null

此成员是否提供给 model。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员将从所提供的 schema 中移除。

ComputerCursorPositionInput
object
{
}

获取光标的当前 (x, y) 像素坐标。

ComputerCursorPositionToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerDoubleClickConfig
object
{
defer_loading
,
enabled
}

double_click
的 config 覆盖项。

defer_loading
:
optional
boolean
或
null
延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值按成员而定，具体见 toolset 的文档。enabled 解析为 false 的成员不会出现在所提供的 schema 中。

ComputerDoubleClickInput
object
{
coordinate
,
text
}

在指定的 (x, y) 像素坐标处双击鼠标左键，或
如果省略
coordinate
，则在当前光标位置双击。

coordinate
:
optional
array of
number
or
null

(x, y)：x 像素为距左边缘的距离，y 像素为距上边缘的距离。
minItems
2
maxItems
2
text
:
optional
string
or
null

在此操作期间按住的可选键组合（例如 "ctrl"、"shift"、"ctrl+shift"）。

ComputerDoubleClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerHoldKeyConfig
object
{
defer_loading
,
enabled
}

hold_key
的配置覆盖。
defer_loading
:
optional
boolean
or
null

延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值按成员而定，具体见 toolset 的文档。enabled 解析为 false 的成员不会出现在所提供的 schema 中。

ComputerHoldKeyInput
object
{
duration
,
text
}

按住一个键或键组合一段指定的时长。使用与
key
相同的键
语法。

duration
:
number

按住键的时长，以秒为单位。
maximum
300
text
:
string

要按住的键或键组合。

ComputerHoldKeyToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerKeyConfig
object
{
defer_loading
,
enabled
}

key
的配置覆盖。
defer_loading
:
optional
boolean
or
null

延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值按成员而定，具体见 toolset 的文档。enabled 解析为 false 的成员不会出现在所提供的 schema 中。
Whether this member is offered to the model. Default is per member, per the toolset's documentation. A member whose enabled resolves false is withheld from the served schema.

ComputerKeyInput
object
{
text
,
repeat
}

在键盘上按下一个键或一组组合键。使用 "+" 组合修饰键与按键（例如 "ctrl+s"、"alt+Tab"、"ctrl+shift+Escape"）。按键名称不区分大小写；支持常见名称，如 "Return"、"Tab"、"Escape"、"Up"、"Down"、"Left"、"Right"、"Home"、"End"、"Page_Up"、"Page_Down"、"Delete"、"BackSpace"。

text
:
string

要按下的键或组合键。

repeat
:
optional
number
or
null

按键重复的次数。默认值为 1。
minimum
1
maximum
100

ComputerKeyToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerLeftClickConfig
object
{
defer_loading
,
enabled
}

left_click
的配置覆盖项。

defer_loading
:
optional
boolean
or
null

为此成员延迟加载。在 toolset 的每个 enabled 成员上必须解析为相同的值。

enabled
:
optional
boolean
or
null

是否将此成员提供给模型。默认值按每个成员、依据 toolset 的文档确定。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

ComputerLeftClickDragConfig
object
{
defer_loading
,
enabled
}

left_click_drag
的配置覆盖项。

defer_loading
:
optional
boolean
or
null

为此成员延迟加载。在 toolset 的每个 enabled 成员上必须解析为相同的值。

enabled
:
optional
boolean
or
null

是否将此成员提供给模型。默认值按每个成员、依据 toolset 的文档确定。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

ComputerLeftClickDragInput
object
{
coordinate
,
start_coordinate
,
text
}

将光标从
start_coordinate
拖拽到
coordinate
。

coordinate
:
array of
number

(x, y)：x 为距左边缘的像素数，y 为距上边缘的像素数。
minItems
2
maxItems
2

start_coordinate
:
array of

```
number

(x, y)：x 像素距离左边缘，y 像素距离上边缘。
minItems
2
maxItems
2
text
:
optional
string
or
null

在此操作期间可选按住的组合键（例如 "ctrl"、"shift"、"ctrl+shift"）。

ComputerLeftClickDragToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


ComputerLeftClickInput
object
{
coordinate
,
text
}

在指定的 (x, y) 像素坐标处点击鼠标左键，若省略
coordinate
，则在当前光标位置点击。

coordinate
:
optional
array of
number
or
null

(x, y)：x 像素距离左边缘，y 像素距离上边缘。
minItems
2
maxItems
2
text
:
optional
string
or
null

在此操作期间可选按住的组合键（例如 "ctrl"、"shift"、"ctrl+shift"）。

ComputerLeftClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


ComputerLeftMouseDownConfig
object
{
defer_loading
,
enabled
}

left_mouse_down
的 config 覆盖项。
defer_loading
:
optional
boolean
or
null

延迟加载此成员。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员将从所提供的 schema 中隐去。
ComputerLeftMouseDownInput
object
{
}

在当前光标位置按下并按住鼠标左键。

ComputerLeftMouseDownToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}


ComputerLeftMouseUpConfig
object
{
defer_loading
,
enabled
}

left_mouse_up
的 config 覆盖项。
defer_loading
:
optional
boolean
or
null

延迟加载此成员。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给模型。默认值因成员而异，参见 toolset 的文档。enabled 解析为 false 的成员将从所提供的 schema 中隐去。
ComputerLeftMouseUpInput
object
{
}
```

释放鼠标左键。

ComputerLeftMouseUpToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerMiddleClickConfig
object
{
defer_loading
,
enabled
}

middle_click 的 config 覆盖项。
defer_loading
:
optional
boolean
or
null

延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，依 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

ComputerMiddleClickInput
object
{
coordinate
,
text
}

在指定的 (x, y) 像素坐标处点击鼠标中键；若省略
coordinate
，则在当前光标位置点击。

coordinate
:
optional
array of
number
or
null

(x, y)：x 为距左边缘的像素数，y 为距上边缘的像素数。
minItems
2
maxItems
2
text
:
optional
string
or
null

在此操作期间按住的可选按键组合（例如 "ctrl"、"shift"、"ctrl+shift"）。

ComputerMiddleClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerMouseMoveConfig
object
{
defer_loading
,
enabled
}

mouse_move 的 config 覆盖项。
defer_loading
:
optional
boolean
or
null

延迟加载此成员。在 toolset 的每个 enabled 成员上必须解析为相同的值。
enabled
:
optional
boolean
or
null

此成员是否提供给 model。默认值按成员而定，依 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中扣留。

ComputerMouseMoveInput
object
{
coordinate
}

将光标移动到指定的 (x, y) 像素坐标。仅用于悬停而不点击；否则请直接使用点击操作。

coordinate
:
array of
number

(x, y)：x 为距左边缘的像素数，y 为距上边缘的像素数。
minItems
2
maxItems
2

ComputerMouseMoveToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerRightClickConfig
object
{
defer_loading
,
enabled
}
right_click
的配置覆盖。
defer_loading
：
optional
boolean
或
null
延迟加载此成员。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
：
optional
boolean
或
null
是否将此成员提供给模型。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员会从提供的 schema 中隐去。
ComputerRightClickInput
object
{
coordinate
,
text
}
在指定的 (x, y) 像素坐标处点击鼠标右键，如果省略
coordinate
，则在当前光标位置点击。
coordinate
：
optional
array of
number
或
null
(x, y)：x 为距左边缘的像素数，y 为距上边缘的像素数。
minItems
2
maxItems
2
text
：
optional
string
或
null
在此操作期间按住的可选按键组合（例如 "ctrl"、"shift"、"ctrl+shift"）。
ComputerRightClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
ComputerScreenshotConfig
object
{
defer_loading
,
enabled
}
screenshot
的配置覆盖。
defer_loading
：
optional
boolean
或
null
延迟加载此成员。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
：
optional
boolean
或
null
是否将此成员提供给模型。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员会从提供的 schema 中隐去。
ComputerScreenshotInput
object
{
}
截取屏幕截图。
ComputerScreenshotToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}
ComputerScrollConfig
object
{
defer_loading
,
enabled
}
scroll
的配置覆盖。
defer_loading
：
optional
boolean
或
null
延迟加载此成员。必须在 toolset 的每个 enabled 成员上解析为相同的值。
enabled
：
optional
boolean
或
null
该成员是否提供给模型。默认值按成员而定，参见 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中移除。

ComputerScrollDirection
=

"up"
或
"down"
或
"left"
或
"right"

以下之一：
"up"
"down"
"left"
"right"

ComputerScrollInput
object
{
scroll_amount
,
scroll_direction
,
coordinate
,
text
}

在指定的 (x, y) 像素坐标处滚动屏幕；若省略
coordinate
，则在当前光标位置滚动。不要使用 PageUp/PageDown 来滚动。

scroll_amount
:
number

滚轮的 "click" 次数。

scroll_direction
:
ComputerScrollDirection

以下之一：
"up"
"down"
"left"
"right"

coordinate
:
optional
array of
number
或
null

(x, y)：x 为距左边缘的像素数，y 为距顶部边缘的像素数。
minItems
2
maxItems
2

text
:
optional
string
或
null

在此操作期间要按住的按键组合（可选）（例如 "ctrl"、"shift"、"ctrl+shift"）。

ComputerScrollToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerToolUseBlock
=

ComputerKeyToolUseBlock
或
ComputerHoldKeyToolUseBlock
或
ComputerTypeToolUseBlock
或
14
more

以下之一：

ComputerToolset20260801
object
{
type
:
"computer_toolset_20260801"
,
cache_control
,
configs
}

computer toolset：单个
tools[]
条目（不带
name
），用于声明 computer tool 家族。模型被服务的是该家族的工具，其中通过
configs
禁用的成员会从 schema 中移除。默认所有成员都启用，包括 zoom。单工具选项
display_number
和
enable_zoom
不是 toolset 条目的字段——它只携带
type
、
configs
和
cache_control
；zoom 通过
configs.zoom.enabled
控制。

ComputerToolsetConfigs
object
{
type
,
cursor_position
,
double_click
,
14
more
}

computer_toolset_20260801
的按成员配置：每个成员工具对应一个 optional 字段，以成员名称作为键——即该成员的
tool_use
blocks carry. Every member is an
accepted key, and a member's defaults apply wherever its key is
absent. Unknown keys are rejected: the field set is this toolset
version's complete member set.

ComputerTripleClickConfig
object
{
defer_loading
,
enabled
}

triple_click
's config overrides.
defer_loading
:
optional
boolean
or
null

Defer loading for this member. Must resolve to the same value on every enabled member of the toolset.
enabled
:
optional
boolean
or
null

Whether this member is offered to the model. Default is per member, per the toolset's documentation. A member whose enabled resolves false is withheld from the served schema.

ComputerTripleClickInput
object
{
coordinate
,
text
}

Triple-click the left mouse button at the specified (x, y) pixel coordinate, or
the current cursor position if
coordinate
is omitted.

coordinate
:
optional
array of
number
or
null

(x, y): x pixels from the left edge, y pixels from the top edge.
minItems
2
maxItems
2
text
:
optional
string
or
null

Optional key combination to hold down during this action (e.g. "ctrl", "shift", "ctrl+shift").

ComputerTripleClickToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerTypeConfig
object
{
defer_loading
,
enabled
}

type
's config overrides.
defer_loading
:
optional
boolean
or
null

Defer loading for this member. Must resolve to the same value on every enabled member of the toolset.
enabled
:
optional
boolean
or
null

Whether this member is offered to the model. Default is per member, per the toolset's documentation. A member whose enabled resolves false is withheld from the served schema.

ComputerTypeInput
object
{
text
}

Type a string of text on the keyboard.
text
:
string

The text to type.

ComputerTypeToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
more
}

ComputerWaitConfig
object
{
defer_loading
,
enabled
}

wait
's config overrides.
defer_loading
:
optional
boolean
or
null
为此成员延迟加载。在 toolset 的每个 enabled 成员上都必须解析为相同的值。
enabled
:
optional
boolean
或
null
此成员是否提供给 model。默认值按成员确定，依据 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中隐去。
ComputerWaitInput
object
{
duration
}
等待指定的时长。
duration
:
number
等待时长，单位为秒。
maximum
300
ComputerWaitToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3 more
}
ComputerZoomConfig
object
{
defer_loading
,
enabled
}
zoom 的配置覆盖项。
defer_loading
:
optional
boolean
或
null
为此成员延迟加载。在 toolset 的每个 enabled 成员上都必须解析为相同的值。
enabled
:
optional
boolean
或
null
此成员是否提供给 model。默认值按成员确定，依据 toolset 的文档。enabled 解析为 false 的成员会从所提供的 schema 中隐去。
ComputerZoomInput
object
{
region
}
截取矩形区域的截图。区域坐标位于 full-screenshot 空间（而非物理显示像素）。裁剪结果会被放大以填满 image budget，从而使精细细节变得清晰可辨。
region
:
array of
number
(x0, y0, x1, y1)：要截取的区域。
minItems
4
maxItems
4
ComputerZoomToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3 more
}
Container
object
{
id
,
expires_at
,
skills
}
有关请求中所用 container 的信息（供 code execution tool 使用）
id
:
string
此请求中所用 container 的标识符
expires_at
:
string
container 将过期的时间。
format
date-time
skills
:
array of
ContainerSkill
{
type
,
skill_id
,
version
}
或
null
container 中加载的 Skills
type
:
"anthropic"
或
"custom"
skill 的类型 —— 'anthropic'（内置）或 'custom'（用户自定义）
以下之一：
"anthropic"
"custom"
skill_id
:
string
Skill ID
minLength
1
maxLength
64
version

```
string
解析后的版本：custom skills 的 skill version ID。
minLength
1
maxLength
64

ContainerParams
object
{
id
,
skills
}
带有要加载的 skills 的 container 参数。
id
:
optional
string
or
null

Container id

skills
:
optional
array of
SkillParams
{
type
,
skill_id
,
version
}
or
null

要在 container 中加载的 skills 列表
maxItems
20

type
:
"anthropic"
or
"custom"

skill 的类型 - 'anthropic'（内置）或 'custom'（用户自定义）
以下之一：
"anthropic"

"custom"


skill_id
:
string

Skill ID
minLength
1
maxLength
64

version
:
optional
string

skill 版本，或 'latest' 表示最新版本
minLength
1
maxLength
64

ContainerSkill
object
{
type
,
skill_id
,
version
}

已在 container 中加载的 skill（response model）。

type
:
"anthropic"
or
"custom"

skill 的类型 - 'anthropic'（内置）或 'custom'（用户自定义）
以下之一：
"anthropic"

"custom"


skill_id
:
string

Skill ID
minLength
1
maxLength
64

version
:
string

解析后的版本：custom skills 的 skill version ID。
minLength
1
maxLength
64

ContainerUploadBlock
object
{
type
:
"container_upload"
,
file_id
}

上传到 container 的文件的 response model。

type
:
"container_upload"

default
container_upload
file_id
:
string


ContainerUploadBlockParam
object
{
type
:
"container_upload"
,
file_id
,
cache_control
}

表示要上传到 container 的文件的内容块
通过此块上传的文件将在 container 的输入目录中可用。
type
:
"container_upload"

file_id
:
string


cache_control
:
optional
CacheControlEphemeral
{
type
:
"ephemeral"
,
ttl
}
or
null

在此内容块处创建 cache control 断点。
type
:
"ephemeral"


ttl
:
optional
"5m"
or
"1h"

cache control 断点的 time-to-live。
其值可以是以下之一：
5m
: 5 分钟
1h
: 1 小时
默认为
5m
。详情请参阅
prompt caching pricing
。
以下之一：
"5m"
```

"1h"

ContentBlock
=

TextBlock
or
ThinkingBlock
or
RedactedThinkingBlock
or
9
more

One of the following:

ContentBlockParam
=

TextBlockParam
or
ImageBlockParam
or
DocumentBlockParam
or
13
more

One of the following:

ContentBlockSource
object
{
type
:
"content"
,
content
}

type
:
"content"

content
:
string
or
array of
ContentBlockSourceContent

One of the following:

string

ContentBlockSourceContent
=

array of
ContentBlockSourceContent

One of the following:

TextBlockParam
object
{
type
:
"text"
,
text
,
cache_control
,
citations
}

ImageBlockParam
object
{
type
:
"image"
,
source
,
cache_control
,
transformations
}

ContentBlockSourceContent
=

TextBlockParam
or
ImageBlockParam

One of the following:

TextBlockParam
object
{
type
:
"text"
,
text
,
cache_control
,
citations
}

ImageBlockParam
object
{
type
:
"image"
,
source
,
cache_control
,
transformations
}

Diagnostics
object
{
cache_miss_reason
}

请求级 diagnostics：说明为什么 prompt cache 无法完全复用由
diagnostics.previous_message_id
所指定请求的前缀。

cache_miss_reason
:
CacheMissReason
or
null

解释为什么 prompt cache 无法完全复用由
diagnostics.previous_message_id
所标识请求的前缀。
null
表示诊断仍在进行中——响应在后台比较完成之前就已被序列化。
One of the following:

DiagnosticsParam
object
{
previous_message_id
}

请求级 diagnostics。目前携带上一条响应
id，用于 prompt-cache 差异报告。

previous_message_id
:
optional
string
or
null

来自此客户端上一条 /v1/messages 响应的
id
（
msg_...
）。服务器会将那个请求的 prompt 指纹与此请求的进行比对，并在 prompt-cache 前缀无法被复用时返回
diagnostics.cache_miss_reason
。在第一轮传入
null
以表示选择启用且没有可比较的先前消息。
maxLength
256

DirectCaller
object
{
type
:
"direct"
}
直接从模型进行工具调用。
type
:
"direct"

DocumentBlock
object
{
type
:
"document"
,
citations
,
source
,
title
}

DocumentBlockParam
object
{
type
:
"document"
,
source
,
cache_control
,
3
more
}

EncryptedCodeExecutionResultBlock
object
{
type
:
"encrypted_code_execution_result"
,
content
,
encrypted_stdout
,
2
more
}

用于 PFC + web_search 结果的带加密 stdout 的代码执行结果。
type
:
"encrypted_code_execution_result"

default
encrypted_code_execution_result

content
:
array of
CodeExecutionOutputBlock
{
type
:
"code_execution_output"
,
file_id
}

type
:
"code_execution_output"

default
code_execution_output
file_id
:
string

encrypted_stdout
:
string

return_code
:
number

stderr
:
string

EncryptedCodeExecutionResultBlockParam
object
{
type
:
"encrypted_code_execution_result"
,
content
,
encrypted_stdout
,
2
more
}

用于 PFC + web_search 结果的带加密 stdout 的代码执行结果。
type
:
"encrypted_code_execution_result"

content
:
array of
CodeExecutionOutputBlockParam
{
type
:
"code_execution_output"
,
file_id
}

type
:
"code_execution_output"

file_id
:
string

encrypted_stdout
:
string

return_code
:
number

stderr
:
string

FileDocumentSource
object
{
type
:
"file"
,
file_id
}

type
:
"file"

file_id
:
string

FileImageSource
object
{
type
:
"file"
,
file_id
}

type
:
"file"

file_id
:
string

ImageBlockParam
object
{
type
:
"image"
,
source
,
cache_control
,
transformations
}

ImageTransformationsParam
object
{
oversized_image
}

配置服务器在模型观测此图像之前对其应用的变换。每个键命名服务器对其执行变换的一个条件；其值选择所应用的变换。省略的键保持其默认行为，空对象等同于省略该字段。

oversized_image
:
optional
"downsize"
or
"error"

当此图像超出模型的最大图像尺寸时服务器的行为。
"downsize"
（默认）会缩小图像以使其适配，这会改变模型所观测到的尺寸，而不会告诉你。
"error"
则用一个 400 error 拒绝该请求，并在错误中指明图像的尺寸以及可容纳的最大尺寸，这样你可以有意地缩放图像——你的图像永远不会被静默缩小。
以下之一：
"downsize"

"error"

InputJSONDelta
object
{
type
:
"input_json_delta"
,
partial_json
}

type
:
"input_json_delta"

default
input_json_delta
partial_json
:
string

JSONOutputFormat
object
{
type
:
"json_schema"
,
schema
}

type
:
"json_schema"

schema
:
map
[
unknown
]

该格式的 JSON schema

MemoryTool20250818
object
{
type
:
"memory_20250818"
,
name
,
allowed_callers
,
另有 4 个
}

Message
object
{
type
:
"message"
,
id
,
container
,
另有 8 个
}

MessageCountTokensTool
=

Tool
或
ToolBash20250124
或
CodeExecutionTool20250522
或
另有 18 个

以下之一：

MessageCreateParamsContainer
=

ContainerParams
或
string

用于跨请求复用的 Container 标识符。
以下之一：

ContainerParams
object
{
id
,
skills
}

带有待加载 skills 的 Container 参数。
id
:
optional
string
或
null

Container id

skills
:
optional
array of
SkillParams
{
type
,
skill_id
,
version
}
或
null

要在 container 中加载的 skills 列表
maxItems
20

type
:
"anthropic"
或
"custom"

skill 的类型——'anthropic'（内置）或 'custom'（用户自定义）
以下之一：
"anthropic"

"custom"

skill_id
:
string

Skill ID
minLength
1
maxLength
64

version
:
optional
string

Skill 版本，或 'latest' 表示最新版本
minLength
1
maxLength
64
string

MessageDeltaUsage
object
{
cache_creation_input_tokens
,
cache_read_input_tokens
,
input_tokens
,
另有 3 个
}

MessageParam
object
{
content
,
role
}

MessageTokensCount
object
{
input_tokens
}

input_tokens
:
number

所提供的 messages 列表、system prompt 和 tools 中 token 的总数。

Metadata
object
{
user_id
}

```
user_id : optional string 或 null
```

与请求相关联的用户的外部标识符。
这应当是 uuid、hash 值或其他不透明标识符。Anthropic 可能会使用此 id 来帮助检测滥用行为。不要包含任何可识别身份的信息，例如姓名、电子邮件地址或电话号码。

```
maxLength
512
```

```
Model
=
"claude-haiku-5-5"
or
"claude-sonnet-5-5"
or
"claude-fable-5-1"
or
另外 17 个
or
string
```

将完成你的 prompt 的 model。
有关更多详细信息和选项，请参阅 models。

以下之一：

```
OutputConfig
object
{
effort
,
format
}
```

```
effort
:
optional
"low"
or
"medium"
or
"high"
or
另外 2 个
or
null
```

model 应在响应中投入多少 effort。更高的 effort 级别可能会带来更详尽的分析，但耗时更长。
有效值为 low、medium、high、xhigh 或 max。

以下之一：

```
"low"
```

```
"medium"
```

```
"high"
```

```
"xhigh"
```

```
"max"
```

```
format
:
optional
JSONOutputFormat
{
type
:
"json_schema"
,
schema
}
or
null
```

用于指定 Claude 在响应中的输出格式的 schema。请参阅 structured outputs

```
type
:
"json_schema"
```

```
schema
:
map
[
unknown
]
```

该格式的 JSON schema

```
OutputTokensDetails
object
{
thinking_tokens
}
```

```
thinking_tokens
:
number
```

model 作为内部推理生成的 output token 数量，包括 thinking-block 分隔符 token。
反映的是 model 产生的原始推理，而不是响应体中返回的（可能更短的）摘要 thinking 文本。通过对原始推理文本重新 tokenize 计算得出，因此可能与 model 的精确生成计数相差少量 token。始终 ≤ output_tokens；
output_tokens - thinking_tokens 近似于非推理部分的输出。

```
default
0
```

```
minimum
0
```

```
PlainTextSource
object
{
type
:
"text"
,
data
,
media_type
}
```

```
type
:
"text"
```

```
data
:
string
```

```
media_type
:
"text/plain"
```

```
RawContentBlockDelta
=
TextDelta
or
InputJSONDelta
or
CitationsDelta
or
另外 2 个
```

以下之一：

```
RawContentBlockDeltaEvent
object
{
type
:
```

{
"content_block_delta"
,
delta
,
index
}


type
:
"content_block_delta"

default
content_block_delta

delta
:
RawContentBlockDelta

以下之一：
index
:
number


RawContentBlockStartEvent
object
{
type
:
"content_block_start"
,
content_block
,
index
}


RawContentBlockStopEvent
object
{
type
:
"content_block_stop"
,
index
}


type
:
"content_block_stop"

default
content_block_stop
index
:
number


RawMessageDeltaEvent
object
{
type
:
"message_delta"
,
delta
,
usage
}


RawMessageStartEvent
object
{
type
:
"message_start"
,
message
}


type
:
"message_start"

default
message_start

message
:
Message
{
type
:
"message"
,
id
,
container
,
8
more
}


RawMessageStopEvent
object
{
type
:
"message_stop"
}


type
:
"message_stop"

default
message_stop

RawMessageStreamEvent
=

RawMessageStartEvent
or
RawMessageDeltaEvent
or
RawMessageStopEvent
or
3
more

以下之一：

RedactedThinkingBlock
object
{
type
:
"redacted_thinking"
,
data
}


type
:
"redacted_thinking"

default
redacted_thinking

data
:
string

此 redacted thinking block 的内容，当模型的 thinking 部分因安全原因被 redact 时返回。该字段不透明且已加密，无可读内容。
在继续多轮对话时，将
redacted_thinking
blocks 原样传回 API。
详情请参阅
extended thinking
。

RedactedThinkingBlockParam
object
{
type
:
"redacted_thinking"
,
data
}

type
:
"redacted_thinking"

data
:
string

此 redacted thinking block 的
data
值，与之前响应中 API 返回的完全一致。不透明且已加密；请原样传回。

RefusalStopDetails
object
{
type
:
"refusal"
,
category
,
explanation
}

有关 refusal 的结构化信息。

type
:
"refusal"

default
refusal

category
:
"cyber"
or
"bio"
or
"frontier_llm"
or
2
more
or
null

触发该 refusal 的策略类别。
当 refusal 不映射到具名类别时为
null
。
以下之一：
"cyber"

该请求可能助长网络危害，例如恶意软件或漏洞利用开发。正常的网络安全工作也可能触发此类别。
"bio"
该请求可能助长生物危害，例如危险的实验室方法。有益的生命科学工作也可能触发此类别。
"frontier_llm"
该请求可能协助开发竞争性 AI 模型，这在 Anthropic 的商业条款下受到限制。正常的机器学习工作也可能触发此类别。
"reasoning_extraction"
该请求要求模型在响应文本中复现其内部推理。若要以结构化形式获取推理，请使用自适应思考。
"general_harms"
该请求可能与某个被判定为有害的领域相关。正常工作有时也可能触发此类别。
explanation：
string 或 null
拒绝的人类可读解释。
此文本不保证稳定。
当该类别没有可用解释时为 null。
SearchResultBlockParam
object
{
type:
"search_result"
,
content
,
source
,
3
more
}
ServerToolCaller
object
{
type:
"code_execution_20250825"
,
tool_id
}
由服务端工具生成的工具调用。
type:
"code_execution_20250825"
tool_id:
string
pattern
^srvtoolu_[a-zA-Z0-9_]+$
ServerToolCaller20260120
object
{
type:
"code_execution_20260120"
,
tool_id
}
type:
"code_execution_20260120"
tool_id:
string
pattern
^srvtoolu_[a-zA-Z0-9_]+$
ServerToolUsage
object
{
web_fetch_requests
,
web_search_requests
}
web_fetch_requests:
number
web fetch 工具请求的数量。
default
0
minimum
0
web_search_requests:
number
web search 工具请求的数量。
default
0
minimum
0
ServerToolUseBlock
object
{
type:
"server_tool_use"
,
id
,
caller
,
2
more
}
ServerToolUseBlockParam
object
{
type:
"server_tool_use"
,
id
,
input
,
3
more
}
SignatureDelta
object
{
type:
"signature_delta"
,
signature
}
type:
"signature_delta"
default
signature_delta
signature
:
string

此 thinking block 的
signature
：一个不透明值，用于在将该 block 传回 API 时验证其由 Claude 生成。通过
signature_delta
事件传递，紧接在该 block 的
content_block_stop
事件之前。

SkillParams
object
{
type
,
skill_id
,
version
}

要在容器中加载的 skill 的规范（request model）。

type
:
"anthropic"
或
"custom"

skill 类型 - 为 'anthropic'（内置）或 'custom'（用户定义）
以下之一：
"anthropic"

"custom"


skill_id
:
string

Skill ID
minLength
1
maxLength
64

version
:
optional
string

Skill 版本，或 'latest' 表示最新版本
minLength
1
maxLength
64

StopReason
=

"end_turn"
或
"max_tokens"
或
"stop_sequence"
或
4
more

以下之一：
"end_turn"

"max_tokens"

"stop_sequence"

"tool_use"

"pause_turn"

"refusal"

"model_context_window_exceeded"


TextBlock
object
{
type
:
"text"
,
citations
,
text
}


TextBlockParam
object
{
type
:
"text"
,
text
,
cache_control
,
citations
}


TextCitation
=

CitationCharLocation
或
CitationPageLocation
或
CitationContentBlockLocation
或
2
more

以下之一：

TextCitationParam
=

CitationCharLocationParam
或
CitationPageLocationParam
或
CitationContentBlockLocationParam
或
2
more

以下之一：

TextDelta
object
{
type
:
"text_delta"
,
text
}


type
:
"text_delta"

default
text_delta
text
:
string


TextEditorCodeExecutionCreateResultBlock
object
{
type
:
"text_editor_code_execution_create_result"
,
is_file_update
}


type
:
"text_editor_code_execution_create_result"

default
text_editor_code_execution_create_result
is_file_update
:
boolean


TextEditorCodeExecutionCreateResultBlockParam
object
{
type
:
"text_editor_code_execution_create_result"
,
is_file_update
}

type
:
"text_editor_code_execution_create_result"

is_file_update
:
boolean


TextEditorCodeExecutionStrReplaceResultBlock
object
{
type
:
"text_editor_code_execution_str_replace_result"
,
lines
,
new_lines
,
3
另有
}
type
:
"text_editor_code_execution_str_replace_result"
default
text_editor_code_execution_str_replace_result
lines
:
由……组成的 array
string
或
null
new_lines
:
number
或
null
new_start
:
number
或
null
old_lines
:
number
或
null
old_start
:
number
或
null

TextEditorCodeExecutionStrReplaceResultBlockParam
object
{
type
:
"text_editor_code_execution_str_replace_result"
,
lines
,
new_lines
,
3
另有
}
type
:
"text_editor_code_execution_str_replace_result"
lines
:
可选
由……组成的 array
string
或
null
new_lines
:
可选
number
或
null
new_start
:
可选
number
或
null
old_lines
:
可选
number
或
null
old_start
:
可选
number
或
null

TextEditorCodeExecutionToolResultBlock
object
{
type
:
"text_editor_code_execution_tool_result"
,
content
,
tool_use_id
}

TextEditorCodeExecutionToolResultBlockParam
object
{
type
:
"text_editor_code_execution_tool_result"
,
content
,
tool_use_id
,
cache_control
}

TextEditorCodeExecutionToolResultError
object
{
type
:
"text_editor_code_execution_tool_result_error"
,
error_code
,
error_message
}

type
:
"text_editor_code_execution_tool_result_error"
default
text_editor_code_execution_tool_result_error

error_code
:
TextEditorCodeExecutionToolResultErrorCode
以下之一：
"invalid_tool_input"
"unavailable"
"too_many_requests"
"execution_time_exceeded"
"file_not_found"

error_message
:
string
或
null

TextEditorCodeExecutionToolResultErrorCode
=

"invalid_tool_input"
或
"unavailable"
或
"too_many_requests"
或
2
另有
以下之一：
"invalid_tool_input"
"unavailable"
"too_many_requests"
"execution_time_exceeded"
"file_not_found"

TextEditorCodeExecutionToolResultErrorParam
object
{
type
:
"text_editor_code_execution_tool_result_error"
,
error_code
,
error_message
}

type
:
"text_editor_code_execution_tool_result_error"

error_code
:
TextEditorCodeExecutionToolResultErrorCode
以下之一：
"invalid_tool_input"
"unavailable"
"too_many_requests"
"execution_time_exceeded"
"file_not_found"
error_message
：
optional
string
或
null

TextEditorCodeExecutionViewResultBlock
object
{
type
:
"text_editor_code_execution_view_result"
,
content
,
file_type
,
3
more
}
type
:
"text_editor_code_execution_view_result"
default
text_editor_code_execution_view_result
content
:
string
file_type
:
"text"
或
"image"
或
"pdf"
以下之一：
"text"
"image"
"pdf"
num_lines
:
number
或
null
start_line
:
number
或
null
total_lines
:
number
或
null

TextEditorCodeExecutionViewResultBlockParam
object
{
type
:
"text_editor_code_execution_view_result"
,
content
,
file_type
,
3
more
}
type
:
"text_editor_code_execution_view_result"
content
:
string
file_type
:
"text"
或
"image"
或
"pdf"
以下之一：
"text"
"image"
"pdf"
num_lines
:
optional
number
或
null
start_line
:
optional
number
或
null
total_lines
:
optional
number
或
null

ThinkingBlock
object
{
type
:
"thinking"
,
signature
,
thinking
}
type
:
"thinking"
default
thinking
signature
:
string
一个用于验证此 thinking block 是由 Claude 生成的值，当它被传回 API 时使用。
这是一个不透明字段，不应被解释或解析。当将 thinking block 传回 API 时（在使用 extended thinking 的工具时必需），请完全按照接收到的样子传回，并保持此字段不变。
详见
extended thinking
。
thinking
:
string
此 block 中 Claude 思考过程的文本。

ThinkingBlockParam
object
{
type
:
"thinking"
,
signature
,
thinking
}
type
:
"thinking"
signature
:
string
此 thinking block 的
signature
值，需与先前响应中 API 返回的内容完全一致。用于验证该 block 是由 Claude 生成的。
Thinking block 必须未经修改且按原始顺序传回；修改过的 block 会导致 400
invalid_request_error
。
thinking
:
string

API 返回的此块的 thinking 文本。

ThinkingConfigAdaptive
object
{
type
:
"adaptive"
,
display
}

type
:
"adaptive"


display
:
optional
"summarized"
或
"omitted"
或
null

控制 thinking 内容在响应中的呈现方式。当设置为
summarized
时，thinking 正常返回。当设置为
omitted
时，thinking 内容会被隐去，但会返回一个 signature 以支持多轮连续性。默认为
summarized
。
以下之一：
"summarized"

"omitted"


ThinkingConfigBetweenTools
object
{
type
:
"between_tools"
}

type
:
"between_tools"


ThinkingConfigDisabled
object
{
type
:
"disabled"
}

type
:
"disabled"


ThinkingConfigEnabled
object
{
type
:
"enabled"
,
budget_tokens
,
display
}

type
:
"enabled"


budget_tokens
:
number

决定 Claude 可用于其内部推理过程的 token 数量。更大的预算可以为复杂问题启用更彻底的分析，从而提升响应质量。
必须 ≥1024 且小于
max_tokens
。
详情请参阅
extended thinking
。
minimum
1024

display
:
optional
"summarized"
或
"omitted"
或
null

控制 thinking 内容在响应中的呈现方式。当设置为
summarized
时，thinking 正常返回。当设置为
omitted
时，thinking 内容会被隐去，但会返回一个 signature 以支持多轮连续性。默认为
summarized
。
以下之一：
"summarized"

"omitted"


ThinkingConfigParam
=

ThinkingConfigEnabled
或
ThinkingConfigDisabled
或
ThinkingConfigBetweenTools
或
ThinkingConfigAdaptive

用于启用 Claude 扩展思考的配置。
启用后，响应会包含
thinking
内容块，显示 Claude 在最终答案之前的思考过程。需要至少 1,024 个 token 的预算，并计入你的
max_tokens
限制。
详情请参阅
extended thinking
。
以下之一：

ThinkingDelta
object
{
type
:
"thinking_delta"
,
thinking
}


type
:
"thinking_delta"

default
thinking_delta
thinking
:
string

此内容块的增量
thinking
文本。将连续
thinking_delta
事件的
thinking
值拼接起来，以组装该块的完整
thinking
值。

Tool
object
{
type
,
input_schema
,
name
,
7
more
}


ToolBash20250124
object
{
type
:
"bash_20250124"
,
name
,
allowed_callers
,
4
more
}


ToolChoice
=

ToolChoiceAuto
或
ToolChoiceAny
或
ToolChoiceTool
或
ToolChoiceNone

模型应如何使用所提供的tools。模型可以使用特定tool、任何可用tool、自行决定，或完全不使用tools。
以下之一：

ToolChoiceAny
object
{
type
:
"any"
,
disable_parallel_tool_use
}

模型将使用任何可用的tools。
type
:
"any"


disable_parallel_tool_use
:
optional
boolean

是否禁用并行tool使用。
默认值为
false
。如果设置为
true
，模型将恰好输出一次tool使用。

ToolChoiceAuto
object
{
type
:
"auto"
,
disable_parallel_tool_use
}

模型将自动决定是否使用tools。
type
:
"auto"


disable_parallel_tool_use
:
optional
boolean

是否禁用并行tool使用。
默认值为
false
。如果设置为
true
，模型将最多输出一次tool使用。

ToolChoiceNone
object
{
type
:
"none"
}

模型将不被允许使用tools。
type
:
"none"


ToolChoiceTool
object
{
type
:
"tool"
,
name
,
disable_parallel_tool_use
}

模型将使用由
tool_choice.name
指定的tool。
type
:
"tool"

name
:
string

要使用的tool的名称。

disable_parallel_tool_use
:
optional
boolean

是否禁用并行tool使用。
默认值为
false
。如果设置为
true
，模型将恰好输出一次tool使用。

ToolReferenceBlock
object
{
type
:
"tool_reference"
,
tool_name
}


type
:
"tool_reference"

default
tool_reference

tool_name
:
string

minLength
1
maxLength
256
pattern
^[a-zA-Z0-9_-]{1,256}$

ToolReferenceBlockParam
object
{
type
:
"tool_reference"
,
tool_name
,
cache_control
}

可包含在tool_result内容中的tool引用块。
type
:
"tool_reference"


tool_name
:
string

minLength
1
maxLength
256
pattern
^[a-zA-Z0-9_-]{1,256}$

cache_control
:
optional
CacheControlEphemeral
{
type
:
"ephemeral"
,
ttl
}
or
null

在此 content block 处创建一个 cache control 断点。
type
:
"ephemeral"


ttl
:
optional
"5m"
or
"1h"

cache control 断点的 time-to-live。
其值可以是以下之一：
5m
：5 分钟
1h
：1 小时
默认为
5m
。详情请参见
prompt caching pricing
。
以下之一：
"5m"

"1h"


ToolResultBlockParam
object
{
type
:
"tool_result"
,
tool_use_id
,
cache_control
,
另有 3 项
}


ToolSearchToolBm25_20251119
object
{
type
,
name
,
allowed_callers
,
另有 3 项
}


ToolSearchToolRegex20251119
object
{
type
,
name
,
allowed_callers
,
另有 3 项
}


ToolSearchToolResultBlock
object
{
type
:
"tool_search_tool_result"
,
content
,
tool_use_id
}


ToolSearchToolResultBlockParam
object
{
type
:
"tool_search_tool_result"
,
content
,
tool_use_id
,
cache_control
}


ToolSearchToolResultError
object
{
type
:
"tool_search_tool_result_error"
,
error_code
,
error_message
}


type
:
"tool_search_tool_result_error"

default
tool_search_tool_result_error

error_code
:
ToolSearchToolResultErrorCode

以下之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

error_message
:
string
or
null


ToolSearchToolResultErrorCode
=

"invalid_tool_input"
or
"unavailable"
or
"too_many_requests"
or
"execution_time_exceeded"

以下之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"


ToolSearchToolResultErrorParam
object
{
type
:
"tool_search_tool_result_error"
,
error_code
,
error_message
}

type
:
"tool_search_tool_result_error"


error_code
:
ToolSearchToolResultErrorCode

以下之一：
"invalid_tool_input"

"unavailable"

"too_many_requests"

"execution_time_exceeded"

error_message
:
optional
string
or
null


ToolSearchToolSearchResultBlock
object
{
type
:
"tool_search_tool_search_result"
,
tool_references
}


type
:
"tool_search_tool_search_result"

default
tool_search_tool_search_result

tool_references
:
ToolReferenceBlock
的数组
{
type
:
"tool_reference"
,
tool_name
}


type
:
"tool_reference"

default
tool_reference

tool_name
:
string

minLength
1
maxLength
256
pattern
^[a-zA-Z0-9_-]{1,256}$

ToolSearchToolSearchResultBlockParam
object
{
type
:
"tool_search_tool_search_result"
,
tool_references
}


ToolTextEditor20250124
object
{
type
:
"text_editor_20250124"
,
name
,
allowed_callers
,
4
个更多
}


ToolTextEditor20250429
object
{
type
:
"text_editor_20250429"
,
name
,
allowed_callers
,
4
个更多
}


ToolTextEditor20250728
object
{
type
:
"text_editor_20250728"
,
name
,
allowed_callers
,
5
个更多
}


ToolUnion
=

Tool
或
ToolBash20250124
或
CodeExecutionTool20250522
或
18
个更多

以下之一：

ToolUseBlock
object
{
type
:
"tool_use"
,
id
,
caller
,
3
个更多
}


ToolUseBlockParam
object
{
type
:
"tool_use"
,
id
,
input
,
4
个更多
}


ToolUseCaller
=

DirectCaller
或
ServerToolCaller
或
ServerToolCaller20260120

工具调用由哪一方发起：model 直接发起，还是代表其发起某项 server tool。
以下之一：

DirectCaller
object
{
type
:
"direct"
}

直接来自 model 的工具调用。
type
:
"direct"


ServerToolCaller
object
{
type
:
"code_execution_20250825"
,
tool_id
}

由服务端 tool 生成的工具调用。
type
:
"code_execution_20250825"


tool_id
:
string

pattern
^srvtoolu_[a-zA-Z0-9_]+$

ServerToolCaller20260120
object
{
type
:
"code_execution_20260120"
,
tool_id
}

type
:
"code_execution_20260120"


tool_id
:
string

pattern
^srvtoolu_[a-zA-Z0-9_]+$

ToolsetToolUseBlock
=

BrowserToolUseBlock
或
ComputerToolUseBlock
或
ToolUseBlock

以下之一：

URLImageSource
object
{
type
:
"url"
,
url
}

type
:
"url"

url
:
string


URLPDFSource
object
{
type
:
"url"
,
url
}

type
:
"url"

url
:
string


Usage
object
{
cache_creation
,
cache_creation_input_tokens
,
cache_read_input_tokens
,
6
more
}


UserLocation
object
{
type
:
"approximate"
,
city
,
country
,
2
more
}

type
:
"approximate"


city
:
optional
string
or
null

用户所在的城市。
minLength
1
maxLength
255

country
:
optional
string
or
null

用户所在国家的两字母
ISO country code
。
minLength
2
maxLength
2

region
:
optional
string
or
null

用户所在的地区。
minLength
1
maxLength
255

timezone
:
optional
string
or
null

用户的
IANA timezone
。
minLength
1
maxLength
255

WebFetchBlock
object
{
type
:
"web_fetch_result"
,
content
,
retrieved_at
,
url
}


type
:
"web_fetch_result"

default
web_fetch_result

content
:
DocumentBlock
{
type
:
"document"
,
citations
,
source
,
title
}

retrieved_at
:
string
or
null

内容检索时的 ISO 8601 时间戳
url
:
string

抓取内容的 URL

WebFetchBlockParam
object
{
type
:
"web_fetch_result"
,
content
,
url
,
retrieved_at
}

type
:
"web_fetch_result"


content
:
DocumentBlockParam
{
type
:
"document"
,
source
,
cache_control
,
3
more
}

url
:
string

抓取内容的 URL
retrieved_at
:
optional
string
or
null

内容检索时的 ISO 8601 时间戳

WebFetchTool20250910
object
{
type
:
"web_fetch_20250910"
,
name
,
allowed_callers
,
9
more
}


WebFetchTool20260209
object
{
type
:
"web_fetch_20260209"
,
name
,
allowed_callers
,
9
more
}


WebFetchTool20260309
object
{
type
:
"web_fetch_20260309"
,
name
,
allowed_callers
,
10
more
}

带 use_cache 参数的 Web 抓取工具，用于绕过缓存内容。

WebFetchTool20260318
object
{
type
:
"web_fetch_20260318"
,
name
,
allowed_callers
,
11
more
}


WebFetchToolResultBlock
object
{
type
:
"web_fetch_tool_result"
,
caller
,
content
,
tool_use_id
}


WebFetchToolResultBlockParam
object
{
type
:
"web_fetch_tool_result"
,
content
,
tool_use_id
,
2
more
}


WebFetchToolResultErrorBlock
object
{
type
:
"web_fetch_tool_result_error"
,
error_code
}


type
:
"web_fetch_tool_result_error"

default
web_fetch_tool_result_error

error_code
:
WebFetchToolResultErrorCode

以下之一：
"invalid_tool_input"

"url_too_long"

"url_not_allowed"

"url_not_in_prior_context"

"url_not_accessible"

"unsupported_content_type"

"too_many_requests"

"max_uses_exceeded"

"unavailable"

"content_too_large"


WebFetchToolResultErrorBlockParam
object
{
type
:
"web_fetch_tool_result_error"
,
error_code
}

type
:
"web_fetch_tool_result_error"


error_code
:
WebFetchToolResultErrorCode

以下之一：
"invalid_tool_input"

"url_too_long"

"url_not_allowed"

"url_not_in_prior_context"

"url_not_accessible"

"unsupported_content_type"

"too_many_requests"

"max_uses_exceeded"

"unavailable"

"content_too_large"


WebFetchToolResultErrorCode
=

"invalid_tool_input"
或
"url_too_long"
或
"url_not_allowed"
或另外 7 个

以下之一：
"invalid_tool_input"

"url_too_long"

"url_not_allowed"

"url_not_in_prior_context"

"url_not_accessible"

"unsupported_content_type"

"too_many_requests"

"max_uses_exceeded"

"unavailable"

"content_too_large"


WebFetchURLSourceAll
object
{
type
:
"all"
}

源在其中完整贡献的 url_sources 变体：tool filter 的 source 的每一个结果，或所有用户输入。
type
:
"all"


WebFetchURLSourceExcept
object
{
type
:
"except"
,
tools
}

除指定 tools 外每个结果都贡献的 tool filter 变体。
type
:
"except"


tools
:
array of
WebFetchURLSourceToolReference
{
type
:
"tool_reference"
,
name
}

type
:
"tool_reference"

name
:
string


WebFetchURLSourceNone
object
{
type
:
"none"
}

源不贡献任何内容的 url_sources 变体：没有 tool filter 的 source 的任何结果，或没有用户输入。
type
:
"none"


WebFetchURLSourceOnly
object
{
type
:
"only"
,
tools
}

只有指定 tools 的结果贡献的 tool filter 变体。
type
:
"only"


tools
:
array of
WebFetchURLSourceToolReference
{
type
:
"tool_reference"
,
name
}
type
:
"tool_reference"
name
:
string

WebFetchURLSourceToolReference
object
{
type
:
"tool_reference"
,
name
}
type
:
"tool_reference"
name
:
string

tool filter 的 tools 中的一个条目：它必须命名在本请求的 tools[] 中声明的 tool。

WebFetchURLSources
object
{
client_tool_results
,
server_tool_results
,
user_input
}
哪些来源会贡献到 web fetch 可抓取的 URL 集合。每个 key 都是一个带标签的变体：user_input 是 all 或 none；两个 tool filter 是 all、none、only（仅指定 tool 的结果）或 except（除指定 tool 之外的所有结果）。被指定的 tool 必须在本请求的 tools[] 中声明。

WebSearchResultBlock
object
{
type
:
"web_search_result"
,
encrypted_content
,
page_age
,
另有 2 项
}
type
:
"web_search_result"
default
web_search_result
encrypted_content
:
string
page_age
:
string
or
null
title
:
string
url
:
string

WebSearchResultBlockParam
object
{
type
:
"web_search_result"
,
encrypted_content
,
title
,
另有 2 项
}
type
:
"web_search_result"
encrypted_content
:
string
title
:
string
url
:
string
page_age
:
optional
string
or
null

WebSearchTool20250305
object
{
type
:
"web_search_20250305"
,
name
,
allowed_callers
,
另有 7 项
}

WebSearchTool20260209
object
{
type
:
"web_search_20260209"
,
name
,
allowed_callers
,
另有 7 项
}

WebSearchTool20260318
object
{
type
:
"web_search_20260318"
,
name
,
allowed_callers
,
另有 8 项
}

WebSearchToolRequestError
object
{
type
:
"web_search_tool_result_error"
,
error_code
}
type
:
"web_search_tool_result_error"
error_code
:
WebSearchToolResultErrorCode
以下之一：
"invalid_tool_input"
"unavailable"
"max_uses_exceeded"
"too_many_requests"
"query_too_long"
"request_too_large"

WebSearchToolResultBlock
object
{
type
:
"web_search_tool_result"
,
caller
,
content
,
tool_use_id
}

WebSearchToolResultBlockContent
=

WebSearchToolResultError
or
array of
WebSearchResultBlock

以下之一：

WebSearchToolResultBlockParam
object
{
type
:
"web_search_tool_result"
,
content
,
tool_use_id
,
另有 2 项
}

WebSearchToolResultBlockParamContent
=

WebSearchResultBlockParam 的数组
或
WebSearchToolRequestError

以下之一：

WebSearchToolResultError
object
{
type
:
"web_search_tool_result_error"
,
error_code
}

type
:
"web_search_tool_result_error"

默认
web_search_tool_result_error

error_code
:
WebSearchToolResultErrorCode

以下之一：
"invalid_tool_input"
"unavailable"
"max_uses_exceeded"
"too_many_requests"
"query_too_long"
"request_too_large"

WebSearchToolResultErrorCode
=

"invalid_tool_input"
或
"unavailable"
或
"max_uses_exceeded"
或
另有 3 项

以下之一：
"invalid_tool_input"
"unavailable"
"max_uses_exceeded"
"too_many_requests"
"query_too_long"
"request_too_large"

#### Messages Batches

创建 Message Batch
POST
/v1/messages/batches
发送一批 Message 创建请求。

检索 Message Batch
GET
/v1/messages/batches/{message_batch_id}
此端点具有幂等性，可用于轮询 Message Batch 的完成情况。要访问 Message Batch 的结果，请请求响应中的
results_url
字段。

列出 Message Batches
GET
/v1/messages/batches
列出某个 Workspace 中的所有 Message Batches。最近创建的批次会最先返回。

取消 Message Batch
POST
/v1/messages/batches/{message_batch_id}/cancel
可以在处理结束前的任意时间取消 Batches。一旦发起取消，该批次会进入
canceling
状态，此时系统可能会先完成任何正在进行且不可中断的请求，然后再最终完成取消。

删除 Message Batch
DELETE
/v1/messages/batches/{message_batch_id}

检索 Message Batch 结果
GET
/v1/messages/batches/{message_batch_id}/results
将 Message Batch 的结果以
.jsonl
文件流的形式返回。

Ask Docs
