import bpy
import re
import http.client
import json

bl_info = {
    "name": "Ollama AI",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Ollama",
    "description": "Interact with Ollama AI directly inside Blender",
    "category": "Development",
}

class OLLAMA_PT_Panel(bpy.types.Panel):
    bl_label = "Ollama AI"
    bl_idname = "OLLAMA_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ollama'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="Select Model:")
        layout.prop(scene, "ollama_model", text="")
        
        layout.label(text="Custom Model (Optional):")
        row = layout.row()
        row.prop(scene, "ollama_custom_model", text="")

        layout.label(text="System Prompt:")
        layout.prop(scene, "ollama_systemprompt", text="")
        
        layout.label(text="Prompt:")
        layout.prop(scene, "ollama_prompt", text="")
        
        layout.label(text="Specify library (Optional):")
        layout.prop(scene, "ollama_library", text="")
        
        row = layout.row()
        row.prop(scene, "ollama_include_last_response", text="Include Last Response")
        
        row = layout.row()
        row.prop(scene, "ollama_enhance_prompt", text="Enhance Prompt with Steps")
        
        row = layout.row()
        row.operator("ollama.run_prompt", text="Run & Execute")
        
        # Send and Receive prompt buttons on the same line
        row = layout.row()
        row.operator("ollama.send_prompt", text="Send Prompt (avoids freeze)")
        row.operator("ollama.receive_prompt", text="Receive Prompt (wait 10s to 1min)")
        
        layout.label(text="Response:")
        layout.prop(scene, "ollama_response", text="", expand=True)
        
        row = layout.row()
        row.operator("ollama.run_in_scripting", text="Run Response in Scripting Tab")
        
        row = layout.row()
        row.operator("ollama.reset_defaults", text="Reset to Default")

class OLLAMA_OT_RunPrompt(bpy.types.Operator):
    bl_idname = "ollama.run_prompt"
    bl_label = "Run & Execute Prompt with Ollama"
    
    def execute(self, context):
        systemprompt = context.scene.ollama_systemprompt
        prompt = context.scene.ollama_prompt
        library = context.scene.ollama_library
        custom_model = context.scene.ollama_custom_model
        model = context.scene.ollama_model if not custom_model else custom_model
        
        library_text = f"should be {library}. " if library else ""
        
        full_prompt = f"ONLY response with python code. No explanations. Import bpy. The code shall be written for blender. Always keep existing objects. Blender 4.3 \n{systemprompt}\n{library_text}{prompt}"
        
        if context.scene.ollama_enhance_prompt:
            full_prompt += "\nEnhance prompts with steps."
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            conn = http.client.HTTPConnection("localhost", 11434)
            headers = {'Content-type': 'application/json'}
            conn.request("POST", "/api/generate", json.dumps(payload), headers)
            response = conn.getresponse()
            result = response.read().decode()
            conn.close()

            if response.status != 200:
                self.report({'ERROR'}, f"Execution failed: {result}")
                return {'CANCELLED'}

            result = json.loads(result)
            text_response = result.get("response", "")

            text_response = re.sub(r'\b(bpy\.ops\.object)\b', r'# \1', text_response, flags=re.IGNORECASE)
            text_response = re.sub(r'^.*\.remove.*$', r'# \g<0>', text_response, flags=re.IGNORECASE | re.MULTILINE)

            if "import bpy" in text_response:
                text_response = text_response.split("import bpy", 1)[1]
                text_response = "import bpy" + text_response
            
            if "```" in text_response:
                text_response = text_response.split("```")[-2]
            
            text_response = text_response.strip()
            
            context.scene.ollama_response = text_response
            self.report({'INFO'}, "Executed successfully")
            print(text_response)

            def run_in_scripting():
                bpy.context.window.workspace = bpy.data.workspaces['Scripting']
                sanitized_prompt = re.sub(r'[^a-zA-Z0-9_ -]', '', context.scene.ollama_prompt)[:50]  # Keep it clean & short
                text_name = f"Ollama Response - {sanitized_prompt}"
                text_block = bpy.data.texts.new(name=text_name)
                text_block.from_string(text_response)

                def set_active_text():
                    for area in bpy.context.screen.areas:
                        if area.type == 'TEXT_EDITOR':
                            area.spaces.active.text = text_block
                    try:
                        exec(text_response, globals())
                        self.report({'INFO'}, "Executed successfully in Scripting tab")
                    except Exception as e:
                        self.report({'ERROR'}, f"Execution failed: {e}")

                bpy.app.timers.register(set_active_text, first_interval=0.1)

            run_in_scripting()

        except Exception as e:
            self.report({'ERROR'}, f"Execution failed: {e}")
        
        return {'FINISHED'}

class OLLAMA_OT_SendPrompt(bpy.types.Operator):
    bl_idname = "ollama.send_prompt"
    bl_label = "Send Prompt (avoids freeze)"
    
    def execute(self, context):
        systemprompt = context.scene.ollama_systemprompt
        prompt = context.scene.ollama_prompt
        library = context.scene.ollama_library
        custom_model = context.scene.ollama_custom_model
        model = context.scene.ollama_model if not custom_model else custom_model
        
        library_text = f"library should be {library}. " if library else ""
        
        full_prompt = f"ONLY response with python code. No explanations. Import bpy. The code shall be written for blender. Blender 4.3 \n{systemprompt}\n{library_text}{prompt}"
        
        if context.scene.ollama_enhance_prompt:
            full_prompt += "\nEnhance prompts with comments."
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            conn = http.client.HTTPConnection("localhost", 11434)
            headers = {'Content-type': 'application/json'}
            conn.request("POST", "/api/generate", json.dumps(payload), headers)
            bpy.app.driver_namespace["ollama_connection"] = conn
            self.report({'INFO'}, "Prompt sent successfully")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Execution failed: {e}")
        
        return {'CANCELLED'}

class OLLAMA_OT_ReceivePrompt(bpy.types.Operator):
    bl_idname = "ollama.receive_prompt"
    bl_label = "Receive Prompt (avoids freeze)"

    def execute(self, context):
        try:
            conn = bpy.app.driver_namespace.get("ollama_connection", None)
            if conn is None:
                self.report({'ERROR'}, "No connection found! Please send a prompt first.")
                return {'CANCELLED'}

            response = conn.getresponse()
            result = response.read().decode()

            if response.status != 200:
                self.report({'ERROR'}, f"Execution failed: {result}")
                return {'CANCELLED'}

            result = json.loads(result)
            text_response = result.get("response", "")

            if "bpy.ops.object" in text_response:
                text_response = text_response.replace("bpy.ops.object", "# bpy.ops.object")

            if "import bpy" in text_response:
                text_response = text_response.split("import bpy", 1)[1]
                text_response = "import bpy" + text_response

            if "```" in text_response:
                text_response = text_response.split("```")[-2]

            text_response = text_response.strip()

            context.scene.ollama_response = text_response
            self.report({'INFO'}, "Response received successfully")
            print(text_response)

        except Exception as e:
            self.report({'ERROR'}, f"Execution failed: {e}")
        
        return {'FINISHED'}

class OLLAMA_OT_EnhancePrompt(bpy.types.Operator):
    bl_idname = "ollama.enhance_prompt"
    bl_label = "Enhance Prompt with Steps"
    
    def execute(self, context):
        systemprompt = context.scene.ollama_systemprompt
        prompt = context.scene.ollama_prompt
        
        enhanced_prompt = f"{systemprompt}\nenhance prompts with steps. \n{prompt}"
        
        context.scene.ollama_prompt = enhanced_prompt
        self.report({'INFO'}, "Prompt enhanced with steps")
        
        return {'FINISHED'}

class OLLAMA_OT_RunInScripting(bpy.types.Operator):
    bl_idname = "ollama.run_in_scripting"
    bl_label = "Run Response in Scripting Tab"
    
    def execute(self, context):
        response_code = context.scene.ollama_response
        
        if not response_code:
            self.report({'WARNING'}, "No response to run!")
            return {'CANCELLED'}
        
        bpy.context.window.workspace = bpy.data.workspaces['Scripting']
        text_block = bpy.data.texts.new(name="Ollama Response")
        text_block.from_string(response_code)
        
        def set_active_text():
            for area in bpy.context.screen.areas:
                if area.type == 'TEXT_EDITOR':
                    area.spaces.active.text = text_block
            try:
                exec(response_code, globals())
                self.report({'INFO'}, "Executed successfully in Scripting tab")
            except Exception as e:
                self.report({'ERROR'}, f"Execution failed: {e}")

        bpy.app.timers.register(set_active_text, first_interval=0.1)
        
        return {'FINISHED'}

classes = [
    OLLAMA_PT_Panel,
    OLLAMA_OT_RunPrompt,
    OLLAMA_OT_EnhancePrompt,
    OLLAMA_OT_RunInScripting,
    OLLAMA_OT_SendPrompt,
    OLLAMA_OT_ReceivePrompt,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.ollama_systemprompt = bpy.props.StringProperty(name="System Prompt", default="Avoid regular mistakes")
    bpy.types.Scene.ollama_prompt = bpy.props.StringProperty(name="Prompt", default="Make selected object")
    bpy.types.Scene.ollama_library = bpy.props.StringProperty(name="Specify library", default="import random")
    bpy.types.Scene.ollama_response = bpy.props.StringProperty(name="Response", default="")
    bpy.types.Scene.ollama_model = bpy.props.EnumProperty(
        name="Model",
        items=[
            ('qwen2.5-coder:7b', "qwen2.5-coder:7b", ""),
            ('llama3.2:latest', "llama3.2:latest", ""),
            ('deepseek-coder-v2:16b', "deepseek-coder-v2:16b", ""),
        ],
        default='qwen2.5-coder:7b'
    )
    bpy.types.Scene.ollama_custom_model = bpy.props.StringProperty(name="Custom Model", default="")
    bpy.types.Scene.ollama_include_last_response = bpy.props.BoolProperty(name="Include Last Response", default=False)
    bpy.types.Scene.ollama_enhance_prompt = bpy.props.BoolProperty(name="Enhance Prompt with Steps", default=False)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.ollama_systemprompt
    del bpy.types.Scene.ollama_prompt
    del bpy.types.Scene.ollama_library
    del bpy.types.Scene.ollama_response
    del bpy.types.Scene.ollama_model
    del bpy.types.Scene.ollama_custom_model
    del bpy.types.Scene.ollama_include_last_response
    del bpy.types.Scene.ollama_enhance_prompt

if __name__ == "__main__":
    register()
