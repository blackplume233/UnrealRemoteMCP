# EdGraph C++ Tools API Reference

## Calling Convention

All functions are static UFUNCTIONs on `UMCPEdGraphTools`. Call via Python:

```python
from foundation.utility import call_cpp_tools
import unreal

result = call_cpp_tools(unreal.MCPEdGraphTools.handle_xxx, {
    "param1": "value1",
    "param2": 42
})
# result is a dict: {"status": "success", "data": {...}} or {"status": "error", "message": "..."}
```

---

## Functions

### 1. handle_find_graphs_in_asset
Discover EdGraphs inside any asset (Blueprint, BehaviorTree, AnimBP, etc.).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| asset_path | string | yes | `/Game/...` asset path |
| name_filter | string | no | Filter graph paths by substring |
| max_results | int | no | Max graphs to return (default 50) |

**Returns**: `{asset_path, asset_class, graph_count, graphs[{name, path, class, node_count}]}`

### 2. handle_list_graph_nodes
List all nodes in a graph. When `include_properties=true`, each node includes `properties` with ExportText for every UPROPERTY.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | Graph UObject path |
| include_properties | bool | no | Include ExportText properties (default false) |

**Returns**: `{graph_path, graph_name, graph_class, node_count, nodes[{name, path, class, guid, pos_x, pos_y, title, comment, pins[], properties?{}}]}`

### 3. handle_get_graph_node
Get a single node with full details (always includes ExportText properties).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | Graph UObject path |
| node_guid | string | one of | Node GUID |
| node_name | string | one of | Node name |
| node_path | string | one of | Node UObject path |

**Returns**: `{node: {name, path, class, guid, pins[], properties{PropName: {type, export_text}}}}`

### 4. handle_delete_graph_node
Delete a node from graph (breaks all pin links first).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |
| node_guid/node_name/node_path | string | one of | Identify the node |
| auto_save_asset_path | string | no | Asset path to save after |

### 5. handle_set_node_properties
Set editor properties on a node (batch set_editor_property).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |
| node_guid/node_name/node_path | string | one of | |
| properties | object | yes | `{prop_name: value}` |
| auto_save_asset_path | string | no | |

### 6. handle_list_graph_links
List all pin connections in the graph (deduplicated).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |

**Returns**: `{graph_path, link_count, links[{a:{node_guid, node_name, pin}, b:{...}}]}`

### 7. handle_connect_pins
Connect two pins (tries Schema.TryCreateConnection, falls back to MakeLinkTo).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |
| from_node_guid | string | yes | |
| from_pin | string | yes | Pin name on source node |
| to_node_guid | string | yes | |
| to_pin | string | yes | Pin name on target node |
| auto_save_asset_path | string | no | |

### 8. handle_disconnect_pin
Disconnect all links from a specific pin.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |
| node_guid | string | yes | |
| pin_name | string | yes | |
| auto_save_asset_path | string | no | |

### 9. handle_add_comment_node
Add a comment box to the graph.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |
| comment | string | yes | Comment text |
| pos_x, pos_y | number | no | Position |
| width, height | number | no | Size (default 400x100) |
| auto_save_asset_path | string | no | |

### 10. handle_add_node ★
Create any UEdGraphNode subclass. Uses ImportText for property initialization and supports pin default values.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | Target graph UObject path |
| node_class | string | yes | Node class name (short or full path) |
| pos_x, pos_y | number | no | Position in graph |
| import_text | object | no | `{PropertyName: "ImportText value"}` — applied BEFORE AllocateDefaultPins |
| pin_defaults | object | no | `{PinName: "default value"}` — applied AFTER AllocateDefaultPins |

**Returns**: `{node: {full serialized node with properties}, import_errors?: {}, pin_errors?: {}}`

**Execution order**: NewObject → ImportText → PostPlacedNewNode → AllocateDefaultPins → pin_defaults → AddNode

### 11. handle_set_pin_default_value
Set/clear a pin's default value on any node.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| graph_path | string | yes | |
| node_guid | string | yes | |
| pin_name | string | yes | |
| default_value | string | no | Text representation of the value |
| default_object | string | no | Asset path for Object-type pins |
| pin_direction | string | no | "Input" or "Output" to disambiguate |

### 12. handle_compile_asset
Compile a Blueprint-based asset and return diagnostics.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| asset_path | string | yes | |

**Returns**: `{asset_path, status ("success"/"warning"/"error"/"dirty"), has_error, messages[{severity, message}]}`

### 13. handle_create_graph
Create a function or macro graph in a Blueprint.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| asset_path | string | yes | Blueprint asset path |
| graph_name | string | yes | Name for the new graph |
| graph_type | string | no | "function" (default) or "macro" |

**Returns**: `{graph_name, graph_path, graph_class, node_count}`

### 14. handle_delete_graph
Delete a sub-graph from a Blueprint.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| asset_path | string | yes | |
| graph_name | string | one of | |
| graph_path | string | one of | |

### 15. handle_get_asset_info
Query asset metadata: parent class, variables, functions, interfaces, components, all graphs.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| asset_path | string | yes | |

**Returns**: `{asset_class, parent_class, parent_class_path, blueprint_type, variables[], functions[], macros[], interfaces[], components[], graphs[]}`

---

## ImportText Format Reference

The `import_text` parameter in `handle_add_node` uses UE's native property serialization format. Learn formats by inspecting existing nodes with `handle_get_graph_node` (returns `properties.*.export_text`).

### Common Formats

| Type | Format | Example |
|------|--------|---------|
| bool | `"True"` / `"False"` | `"bIsPureFunc": "True"` |
| int32 | `"42"` | |
| float | `"3.14"` | |
| FString | `"Hello World"` | |
| FName | `"MyName"` | |
| Enum | `"Value"` | `"EGPD_Output"` |
| FVector | `"X=1.0 Y=2.0 Z=3.0"` | |
| FRotator | `"P=0.0 Y=90.0 R=0.0"` | |
| UClass* ref | `"/Script/Engine.Actor"` | |
| UObject* ref | `"/Game/Path/To/Asset.Asset"` | |
| FMemberReference | `"(MemberParent=/Script/Engine.KismetSystemLibrary,MemberName=\"PrintString\")"` | |
| FGuid | `"(A=12345678,B=12345678,C=12345678,D=12345678)"` | |

### Learn-by-Example Workflow

```
1. Find an existing node of the same type:
   result = call_cpp_tools(unreal.MCPEdGraphTools.handle_get_graph_node, {
       "graph_path": "...", "node_guid": "..."
   })
   # Inspect result["data"]["node"]["properties"]["FunctionReference"]["export_text"]

2. Copy the export_text, modify the parts you need:
   call_cpp_tools(unreal.MCPEdGraphTools.handle_add_node, {
       "graph_path": "...",
       "node_class": "K2Node_CallFunction",
       "import_text": {
           "FunctionReference": "(MemberParent=/Script/Engine.KismetSystemLibrary,MemberName=\"PrintString\")"
       },
       "pin_defaults": {
           "InString": "Hello World"
       }
   })
```

---

## Common Node Classes

### Flow Control (Blueprint)
- `K2Node_IfThenElse` — Branch
- `K2Node_ExecutionSequence` — Sequence
- `K2Node_DoOnce` — Do Once
- `K2Node_Gate` — Gate
- `K2Node_MultiGate` — Multi Gate
- `K2Node_ForEachArrayLoop` — For Each Loop
- `K2Node_WhileLoop` — While Loop
- `K2Node_Knot` — Reroute node
- `K2Node_Select` — Select

### Functions & Events
- `K2Node_CallFunction` — Function call (needs import_text: FunctionReference)
- `K2Node_Event` — Event (needs import_text: EventReference)
- `K2Node_CustomEvent` — Custom Event (needs import_text: CustomFunctionName)
- `K2Node_FunctionEntry` — Function entry point
- `K2Node_FunctionResult` — Function return node

### Variables
- `K2Node_VariableGet` — Get variable (needs import_text: VariableReference)
- `K2Node_VariableSet` — Set variable (needs import_text: VariableReference)
- `K2Node_Self` — Self reference
- `K2Node_Literal` — Literal value

### Type Operations
- `K2Node_DynamicCast` — Cast (needs import_text: TargetType)
- `K2Node_MakeArray` — Make Array
- `K2Node_MakeStruct` — Make Struct (needs import_text: StructType)
- `K2Node_BreakStruct` — Break Struct (needs import_text: StructType)
- `K2Node_SwitchEnum` — Switch on Enum (needs import_text: Enum)
- `K2Node_SwitchString` — Switch on String
- `K2Node_SwitchInteger` — Switch on Integer

### Utility
- `K2Node_Delay` — Delay (actually a K2Node_CallFunction to Delay)
- `K2Node_InputAction` — Input Action
- `K2Node_Timeline` — Timeline
- `K2Node_SpawnActorFromClass` — Spawn Actor
- `K2Node_GetClassDefaults` — Get Class Defaults
- `K2Node_MakeVariable` — Make variable (local)
- `EdGraphNode_Comment` — Comment box (use handle_add_comment_node instead)

### Animation Blueprint
- `UAnimGraphNode_StateMachine` — State Machine
- `UAnimGraphNode_BlendSpacePlayer` — Blend Space
- `UAnimGraphNode_SequencePlayer` — Animation Sequence
- `UAnimGraphNode_TransitionResult` — Transition
- `UAnimGraphNode_StateResult` — State Result
- `UAnimGraphNode_LinkedAnimLayer` — Linked Anim Layer

### Behavior Tree
- Use `handle_add_node` with `node_class="BTGraphNode"` or BT-specific tools in the `behaviortree` domain.

---

## Complete Blueprint Authoring Workflow

```python
from foundation.utility import call_cpp_tools
import unreal

bp_path = "/Game/MyBlueprint"

# 1. Understand the asset
info = call_cpp_tools(unreal.MCPEdGraphTools.handle_get_asset_info, {"asset_path": bp_path})

# 2. Find the EventGraph
graphs = call_cpp_tools(unreal.MCPEdGraphTools.handle_find_graphs_in_asset, {"asset_path": bp_path})
event_graph_path = graphs["data"]["graphs"][0]["path"]  # typically EventGraph

# 3. List existing nodes
nodes = call_cpp_tools(unreal.MCPEdGraphTools.handle_list_graph_nodes, {
    "graph_path": event_graph_path, "include_properties": True
})

# 4. Create a Branch node
branch = call_cpp_tools(unreal.MCPEdGraphTools.handle_add_node, {
    "graph_path": event_graph_path,
    "node_class": "K2Node_IfThenElse",
    "pos_x": 400, "pos_y": 200
})
branch_guid = branch["data"]["node"]["guid"]

# 5. Create a PrintString call
print_node = call_cpp_tools(unreal.MCPEdGraphTools.handle_add_node, {
    "graph_path": event_graph_path,
    "node_class": "K2Node_CallFunction",
    "pos_x": 700, "pos_y": 200,
    "import_text": {
        "FunctionReference": "(MemberParent=/Script/Engine.KismetSystemLibrary,MemberName=\"PrintString\")"
    },
    "pin_defaults": {
        "InString": "Branch was True!"
    }
})
print_guid = print_node["data"]["node"]["guid"]

# 6. Connect Branch.Then → PrintString.execute
call_cpp_tools(unreal.MCPEdGraphTools.handle_connect_pins, {
    "graph_path": event_graph_path,
    "from_node_guid": branch_guid,
    "from_pin": "Then",
    "to_node_guid": print_guid,
    "to_pin": "execute"
})

# 7. Compile and check
result = call_cpp_tools(unreal.MCPEdGraphTools.handle_compile_asset, {"asset_path": bp_path})
print(result["data"]["status"], result["data"]["messages"])
```

---

## Pin Information

Each pin in serialized node output includes:
- `name` — Pin name
- `direction` — "Input" or "Output"
- `type` — Pin category (exec, bool, float, object, struct, etc.)
- `sub_category` — Pin sub-category (if any)
- `sub_category_object` — Path to sub-category object (UClass/UScriptStruct)
- `is_array`, `is_set`, `is_map`, `is_reference`, `is_const` — Type flags
- `default_value` — Current default value text
- `default_object` — Default object path (for Object pins)
- `auto_generated_default_value` — Engine-generated default
- `linked_to_count` — Number of connections
- `linked_to[]` — Connected pin details
