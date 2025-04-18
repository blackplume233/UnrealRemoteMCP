from typing import Any, Dict, List
from foundation.mcp_app import UnrealMCP
from mcp.server.fastmcp import Context
import unreal
import foundation.utility as unreal_utility
from foundation.utility import call_cpp_tools


# tools reference  https://github.com/chongdashu/unreal-mcp
def register_edit_tool( mcp:UnrealMCP):
    """Register editor tools with the MCP server."""
    @mcp.game_thread_tool()
    def get_actors_in_level(ctx: Context) -> List[Dict[str, Any]]:
        """Get a list of all actors in the current level."""
        all_actors = unreal.MCPEditorTools.handle_get_actors_in_level(unreal_utility.to_unreal_json({}))
        return unreal_utility.to_py_json(all_actors)
    
    @mcp.game_thread_tool()
    def find_actors_by_name(ctx: Context, pattern: str) -> List[str]:
        """Find actors by name pattern."""
        param = {"pattern": pattern}
        all_actors = unreal.MCPEditorTools.handle_get_actors_in_level(unreal_utility.to_unreal_json(param))
        return unreal_utility.to_py_json(all_actors)
        
    
    @mcp.game_thread_tool()
    def spawn_actor(
        ctx: Context,
        name: str,
        type: str,
        location: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = [0.0, 0.0, 0.0]
    ) -> Dict[str, Any]:
        """Create a new actor in the current level.
        
        Args:
            ctx: The MCP context
            name: The name to give the new actor (must be unique)
            type: The type of actor to create (e.g. StaticMeshActor, PointLight)
            location: The [x, y, z] world location to spawn at
            rotation: The [pitch, yaw, roll] rotation in degrees
            
        Returns:
            Dict 
        """
        params = {
                    "name": name,
                    "type": type.upper(),  # Make sure type is uppercase
                    "location": location,
                    "rotation": rotation
        }
        return unreal_utility.to_py_json(unreal.MCPEditorTools.handle_spawn_actor(params))
    
    @mcp.game_thread_tool()
    def delete_actor(ctx: Context, name: str) -> Dict[str, Any]:
        """Delete an actor by name."""
        params = {
                    "name": name,
        }
        json_params = unreal_utility.to_unreal_json(params)
        return unreal_utility.to_py_json(unreal.MCPEditorTools.handle_delete_actor(json_params))
    
    @mcp.game_thread_tool()
    def set_actor_transform(
        ctx: Context,
        name: str,
        location: List[float]  = None,
        rotation: List[float]  = None,
        scale: List[float] = None
    ) -> Dict[str, Any]:
        """Set the transform of an actor by name."""
        params = {
            "name": name,
            "location": location,
            "rotation": rotation,
            "scale": scale
        }
        json_params = unreal_utility.to_unreal_json(params)
        return unreal_utility.to_py_json(unreal.MCPEditorTools.handle_set_actor_transform(json_params))
    
    @mcp.game_thread_tool()
    def get_actor_transform(ctx: Context, path_to_actor: str) -> Dict[str, Any]:
        """Get the transform of an actor by path."""
        actor = unreal.EditorLevelLibrary.get_actor_reference(path_to_actor)
        if actor is None:
            return {"error": "Actor not found"}
        location = actor.get_actor_location()
        rotation = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        return {"location": location, "rotation": rotation, "scale": scale}
    
    @mcp.game_thread_tool()
    def get_actor_properties(ctx: Context, name: str) -> Dict[str, Any]:
        """Get all properties of an actor."""
        params = {
            "name": name,
        }
        return call_cpp_tools(unreal.MCPEditorTools.handle_get_actor_properties, params)
    @mcp.game_thread_tool()
    def set_actor_property(
        ctx: Context,
        name: str,
        property_name: str,
        property_value,
    ) -> Dict[str, Any]:
        """
        Set a property on an actor.
        
        Args:
            name: Name of the actor
            property_name: Name of the property to set
            property_value: Value to set the property to
            
        Returns:
            Dict containing response from Unreal with operation status
        """
        params = {
            "name": name,
            "property_name": property_name,
            "property_value": property_value,
        }
        return call_cpp_tools(unreal.MCPEditorTools.handle_set_actor_property, params)
    @mcp.game_thread_tool()
    def focus_viewport(
        ctx: Context,
        target: str = None,
        location: List[float] = None,
        distance: float = 1000.0,
        orientation: List[float] = None
    ) -> Dict[str, Any]:
        """
        Focus the viewport on a specific actor or location.
        
        Args:
            target: Name of the actor to focus on (if provided, location is ignored)
            location: [X, Y, Z] coordinates to focus on (used if target is None)
            distance: Distance from the target/location
            orientation: Optional [Pitch, Yaw, Roll] for the viewport camera
            
        Returns:
            Response from Unreal Engine
        """
        params = {
            "target": target,
            "location": location,
            "distance": distance,
            "orientation": orientation
        }   
        return call_cpp_tools(unreal.MCPEditorTools.handle_focus_viewport, params)
    @mcp.game_thread_tool()
    def spawn_blueprint_actor(
        ctx: Context,
        blueprint_name: str,
        actor_name: str,
        location: List[float] = [0.0, 0.0, 0.0],
        rotation: List[float] = [0.0, 0.0, 0.0]
    ) -> Dict[str, Any]:
        """Spawn an actor from a Blueprint.
        
        Args:
            ctx: The MCP context
            blueprint_name: Name of the Blueprint to spawn from
            actor_name: Name to give the spawned actor
            location: The [x, y, z] world location to spawn at
            rotation: The [pitch, yaw, roll] rotation in degrees
            
        Returns:
            Dict containing the spawned actor's properties
        """
        params = {
            "blueprint_name": blueprint_name,
            "actor_name": actor_name,
            "location": location,
            "rotation": rotation
        }
        return call_cpp_tools(unreal.MCPEditorTools.handle_spawn_blueprint_actor, params)
    
    
    #region blueprint
    @mcp.game_thread_tool()
    def create_blueprint(
        ctx: Context,
        name: str,
        parent_class: str
    ) -> Dict[str, Any]:
        """Create a new Blueprint class."""
        params = {
            "name": name,
            "parent_class": parent_class
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_create_blueprint, params)
    
    
    @mcp.game_thread_tool()
    def add_component_to_blueprint(
        ctx: Context,
        blueprint_name: str,
        component_type: str,
        component_name: str,
        location: List[float] = [],
        rotation: List[float] = [],
        scale: List[float] = [],
        component_properties: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Add a component to a Blueprint.
        
        Args:
            blueprint_name: Name of the target Blueprint
            component_type: Type of component to add (use component class name without U prefix)
            component_name: Name for the new component
            location: [X, Y, Z] coordinates for component's position
            rotation: [Pitch, Yaw, Roll] values for component's rotation
            scale: [X, Y, Z] values for component's scale
            component_properties: Additional properties to set on the component
        
        Returns:
            Information about the added component
        """
        params = {
            "blueprint_name": blueprint_name,
            "component_type": component_type,
            "component_name": component_name,
            "location": location,
            "rotation": rotation,
            "scale": scale,
            "component_properties": component_properties
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_component_to_blueprint, params)
    
    
    @mcp.game_thread_tool()
    def set_static_mesh_properties(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        static_mesh: str = "/Engine/BasicShapes/Cube.Cube"
    ) -> Dict[str, Any]:
        """
        Set static mesh properties on a StaticMeshComponent.
        
        Args:
            blueprint_name: Name of the target Blueprint
            component_name: Name of the StaticMeshComponent
            static_mesh: Path to the static mesh asset (e.g., "/Engine/BasicShapes/Cube.Cube")
            
        Returns:
            Response indicating success or failure
        """
        params = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "static_mesh": static_mesh
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_set_static_mesh_properties, params)
    @mcp.game_thread_tool()
    def set_component_property(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        property_name: str,
        property_value,
    ) -> Dict[str, Any]:
        """Set a property on a component in a Blueprint."""
        params = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "property_name": property_name,
            "property_value": property_value
        }       
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_set_component_property, params)
    @mcp.game_thread_tool()
    def set_physics_properties(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        simulate_physics: bool = True,
        gravity_enabled: bool = True,
        mass: float = 1.0,
        linear_damping: float = 0.01,
        angular_damping: float = 0.0
    ) -> Dict[str, Any]:
        """Set physics properties on a component."""
        params = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "simulate_physics": simulate_physics,
            "gravity_enabled": gravity_enabled,
            "mass": mass,
            "linear_damping": linear_damping,
            "angular_damping": angular_damping
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_set_physics_properties, params)
    
    @mcp.game_thread_tool()
    def compile_blueprint(
        ctx: Context,
        blueprint_name: str
    ) -> Dict[str, Any]:
        """Compile a Blueprint."""
        params = {
            "blueprint_name": blueprint_name
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_compile_blueprint, params)
    
    @mcp.game_thread_tool()
    def set_blueprint_property(
        ctx: Context,
        blueprint_name: str,
        property_name: str,
        property_value
    ) -> Dict[str, Any]:
        """
        Set a property on a Blueprint class default object.
        
        Args:
            blueprint_name: Name of the target Blueprint
            property_name: Name of the property to set
            property_value: Value to set the property to
            
        Returns:
            Response indicating success or failure
        """
        params = {
            "blueprint_name": blueprint_name,
            "property_name": property_name,
            "property_value": property_value
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_set_blueprint_property, params)   
    
    
    @mcp.game_thread_tool()
    def set_pawn_properties(
        ctx: Context,
        blueprint_name: str,
        auto_possess_player: str = "",
        use_controller_rotation_yaw: bool = None,
        use_controller_rotation_pitch: bool = None,
        use_controller_rotation_roll: bool = None,
        can_be_damaged: bool = None
    ) -> Dict[str, Any]:
        """
        Set common Pawn properties on a Blueprint.
        This is a utility function that sets multiple pawn-related properties at once.
        
        Args:
            blueprint_name: Name of the target Blueprint (must be a Pawn or Character)
            auto_possess_player: Auto possess player setting (None, "Disabled", "Player0", "Player1", etc.)
            use_controller_rotation_yaw: Whether the pawn should use the controller's yaw rotation
            use_controller_rotation_pitch: Whether the pawn should use the controller's pitch rotation
            use_controller_rotation_roll: Whether the pawn should use the controller's roll rotation
            can_be_damaged: Whether the pawn can be damaged
            
        Returns:
            Response indicating success or failure with detailed results for each property
        """
        params = {
            "blueprint_name": blueprint_name,
            "auto_possess_player": auto_possess_player,
            "use_controller_rotation_yaw": use_controller_rotation_yaw,
            "use_controller_rotation_pitch": use_controller_rotation_pitch,
            "use_controller_rotation_roll": use_controller_rotation_roll,   
            "can_be_damaged": can_be_damaged
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_set_pawn_properties, params)
    #endregion
    
    #region node tools
    @mcp.game_thread_tool()
    def add_blueprint_event_node(
        ctx: Context,
        blueprint_name: str,
        event_name: str,
        node_position = None
    ) -> Dict[str, Any]:
        """
        Add an event node to a Blueprint's event graph.
        
        Args:
            blueprint_name: Name of the target Blueprint
            event_name: Name of the event. Use 'Receive' prefix for standard events:
                       - 'ReceiveBeginPlay' for Begin Play
                       - 'ReceiveTick' for Tick
                       - etc.
            node_position: Optional [X, Y] position in the graph
            
        Returns:
            Response containing the node ID and success status
        """
        params = {
            "blueprint_name": blueprint_name,
            "event_name": event_name,
            "node_position": node_position
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_blueprint_event, params)
    
    @mcp.game_thread_tool()
    def add_blueprint_input_action_node(
        ctx: Context,
        blueprint_name: str,
        action_name: str,
        node_position = None
    ) -> Dict[str, Any]:
        """
        Add an input action event node to a Blueprint's event graph.
        
        Args:
            blueprint_name: Name of the target Blueprint
            action_name: Name of the input action to respond to
            node_position: Optional [X, Y] position in the graph
            
        Returns:
            Response containing the node ID and success status
        """
        params = {
            "blueprint_name": blueprint_name,
            "action_name": action_name,
            "node_position": node_position
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_blueprint_input_action_node, params)
    
    @mcp.game_thread_tool()
    def add_blueprint_function_node(
        ctx: Context,
        blueprint_name: str,
        target: str,
        function_name: str,
        params = None,
        node_position = None
    ) -> Dict[str, Any]:
        """
        Add a function call node to a Blueprint's event graph.
        
        Args:
            blueprint_name: Name of the target Blueprint
            target: Target object for the function (component name or self)
            function_name: Name of the function to call
            params: Optional parameters to set on the function node
            node_position: Optional [X, Y] position in the graph
            
        Returns:
            Response containing the node ID and success status
        """
        params = {
            "blueprint_name": blueprint_name,
            "target": target,
            "function_name": function_name,
            "params": params,
            "node_position": node_position  
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_blueprint_function_call, params)
    
    
    @mcp.game_thread_tool()
    def connect_blueprint_nodes(
        ctx: Context,
        blueprint_name: str,
        source_node_id: str,
        source_pin: str,
        target_node_id: str,
        target_pin: str
    ) -> Dict[str, Any]:
        """
        Connect two nodes in a Blueprint's event graph.
        
        Args:
            blueprint_name: Name of the target Blueprint
            source_node_id: ID of the source node
            source_pin: Name of the output pin on the source node
            target_node_id: ID of the target node
            target_pin: Name of the input pin on the target node
            
        Returns:
            Response indicating success or failure
        """
        params = {
            "blueprint_name": blueprint_name,
            "source_node_id": source_node_id,
            "source_pin": source_pin,
            "target_node_id": target_node_id,
            "target_pin": target_pin
        }   
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_connect_blueprint_nodes, params)
    
    @mcp.game_thread_tool()
    def add_blueprint_variable(
        ctx: Context,
        blueprint_name: str,
        variable_name: str,
        variable_type: str,
        is_exposed: bool = False
    ) -> Dict[str, Any]:
        """
        Add a variable to a Blueprint.
        
        Args:
            blueprint_name: Name of the target Blueprint
            variable_name: Name of the variable
            variable_type: Type of the variable (Boolean, Integer, Float, Vector, etc.)
            is_exposed: Whether to expose the variable to the editor
            
        Returns:
            Response indicating success or failure
        """
        params = {
            "blueprint_name": blueprint_name,
            "variable_name": variable_name,
            "variable_type": variable_type,
            "is_exposed": is_exposed
        } 
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_blueprint_variable, params)
    
    @mcp.game_thread_tool()
    def add_blueprint_get_self_component_reference(
        ctx: Context,
        blueprint_name: str,
        component_name: str,
        node_position = None
    ) -> Dict[str, Any]:
        """
        Add a node that gets a reference to a component owned by the current Blueprint.
        This creates a node similar to what you get when dragging a component from the Components panel.
        
        Args:
            blueprint_name: Name of the target Blueprint
            component_name: Name of the component to get a reference to
            node_position: Optional [X, Y] position in the graph
            
        Returns:
            Response containing the node ID and success status
        """
        params = {
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "node_position": node_position
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_blueprint_get_self_component_reference, params)


    @mcp.game_thread_tool()
    def add_blueprint_self_reference(
        ctx: Context,
        blueprint_name: str,
        node_position = None
    ) -> Dict[str, Any]:
        """
        Add a 'Get Self' node to a Blueprint's event graph that returns a reference to this actor.
        
        Args:
            blueprint_name: Name of the target Blueprint
            node_position: Optional [X, Y] position in the graph
            
        Returns:
            Response containing the node ID and success status
        """
        params = {
            "blueprint_name": blueprint_name,
            "node_position": node_position
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_add_blueprint_self_reference, params)
    @mcp.game_thread_tool()
    def find_blueprint_nodes(
        ctx: Context,
        blueprint_name: str,
        node_type = None,
        event_type = None
    ) -> Dict[str, Any]:
        """
        Find nodes in a Blueprint's event graph.
        
        Args:
            blueprint_name: Name of the target Blueprint
            node_type: Optional type of node to find (Event, Function, Variable, etc.)
            event_type: Optional specific event type to find (BeginPlay, Tick, etc.)
            
        Returns:
            Response containing array of found node IDs and success status
        """
        params = {
            "blueprint_name": blueprint_name,
            "node_type": node_type,
            "event_type": event_type
        }
        return call_cpp_tools(unreal.MCPBlueprintTools.handle_find_blueprint_nodes, params)
    #endregion
    
    #region umg tools
    @mcp.game_thread_tool()
    def create_umg_widget_blueprint(
        ctx: Context,
        widget_name: str,
        parent_class: str = "UserWidget",
        path: str = "/Game/UI"
    ) -> Dict[str, Any]:
        """
        Create a new UMG Widget Blueprint.
        
        Args:
            widget_name: Name of the widget blueprint to create
            parent_class: Parent class for the widget (default: UserWidget)
            path: Content browser path where the widget should be created
            
        Returns:
            Dict containing success status and widget path
        """
        params = {
            "widget_name": widget_name,
            "parent_class": parent_class,
            "path": path
        }
        return call_cpp_tools(unreal.MCPUMGTools.handle_create_umg_widget_blueprint, params)
    @mcp.game_thread_tool()
    def add_text_block_to_widget(
        ctx: Context,
        widget_name: str,
        text_block_name: str,
        text: str = "",
        position: List[float] = [0.0, 0.0],
        size: List[float] = [200.0, 50.0],
        font_size: int = 12,
        color: List[float] = [1.0, 1.0, 1.0, 1.0]
    ) -> Dict[str, Any]:
        """
        Add a Text Block widget to a UMG Widget Blueprint.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            text_block_name: Name to give the new Text Block
            text: Initial text content
            position: [X, Y] position in the canvas panel
            size: [Width, Height] of the text block
            font_size: Font size in points
            color: [R, G, B, A] color values (0.0 to 1.0)
            
        Returns:
            Dict containing success status and text block properties
        """
        params = {
            "widget_name": widget_name,
            "text_block_name": text_block_name,
            "text": text,
            "position": position,
            "size": size,
            "font_size": font_size,
            "color": color
        }
        return call_cpp_tools(unreal.MCPUMGTools.handle_add_text_block_to_widget, params)
    @mcp.game_thread_tool()
    def add_button_to_widget(
        ctx: Context,
        widget_name: str,
        button_name: str,
        text: str = "",
        position: List[float] = [0.0, 0.0],
        size: List[float] = [200.0, 50.0],
        font_size: int = 12,
        color: List[float] = [1.0, 1.0, 1.0, 1.0],
        background_color: List[float] = [0.1, 0.1, 0.1, 1.0]
    ) -> Dict[str, Any]:
        """
        Add a Button widget to a UMG Widget Blueprint.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            button_name: Name to give the new Button
            text: Text to display on the button
            position: [X, Y] position in the canvas panel
            size: [Width, Height] of the button
            font_size: Font size for button text
            color: [R, G, B, A] text color values (0.0 to 1.0)
            background_color: [R, G, B, A] button background color values (0.0 to 1.0)
            
        Returns:
            Dict containing success status and button properties
        """
        params = {
            "widget_name": widget_name,
            "button_name": button_name,
            "text": text,
            "position": position,
            "size": size,   
            "font_size": font_size,
            "color": color,
            "background_color": background_color
        }
        return call_cpp_tools(unreal.MCPUMGTools.handle_add_button_to_widget, params)   
    
    @mcp.game_thread_tool()
    def bind_widget_event(
        ctx: Context,
        widget_name: str,
        widget_component_name: str,
        event_name: str,
        function_name: str = ""
    ) -> Dict[str, Any]:
        """
        Bind an event on a widget component to a function.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            widget_component_name: Name of the widget component (button, etc.)
            event_name: Name of the event to bind (OnClicked, etc.)
            function_name: Name of the function to create/bind to (defaults to f"{widget_component_name}_{event_name}")
            
        Returns:
            Dict containing success status and binding information
        """
        params = {
            "widget_name": widget_name,
            "widget_component_name": widget_component_name,
            "event_name": event_name,
            "function_name": function_name
        }   
        return call_cpp_tools(unreal.MCPUMGTools.handle_bind_widget_event, params)
    @mcp.game_thread_tool()
    def add_widget_to_viewport(
        ctx: Context,
        widget_name: str,
        z_order: int = 0
    ) -> Dict[str, Any]:
        """
        Add a Widget Blueprint instance to the viewport.
        
        Args:
            widget_name: Name of the Widget Blueprint to add
            z_order: Z-order for the widget (higher numbers appear on top)
            
        Returns:
            Dict containing success status and widget instance information
        """
        params = {
            "widget_name": widget_name,
            "z_order": z_order
        }
        return call_cpp_tools(unreal.MCPUMGTools.handle_add_widget_to_viewport, params)
    @mcp.game_thread_tool()
    def set_text_block_binding(
        ctx: Context,
        widget_name: str,
        text_block_name: str,
        binding_property: str,
        binding_type: str = "Text"
    ) -> Dict[str, Any]:
        """
        Set up a property binding for a Text Block widget.
        
        Args:
            widget_name: Name of the target Widget Blueprint
            text_block_name: Name of the Text Block to bind
            binding_property: Name of the property to bind to
            binding_type: Type of binding (Text, Visibility, etc.)
            
        Returns:
            Dict containing success status and binding information
        """
        params = {
            "widget_name": widget_name,
            "text_block_name": text_block_name,
            "binding_property": binding_property,
            "binding_type": binding_type
        }
        return call_cpp_tools(unreal.MCPUMGTools.handle_set_text_block_binding, params)
