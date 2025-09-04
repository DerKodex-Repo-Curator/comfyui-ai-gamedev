/**
 * ComfyUI Prompt Display Widget
 * Custom widget for displaying multiline prompts with proper formatting
 */

import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Register custom widget for PromptDisplay nodes
app.registerExtension({
    name: "gamedev.prompt_display",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Check if this is one of our prompt display nodes
        const displayNodes = ["PromptDisplay", "PromptDisplayLarge", "PromptCompare"];
        
        if (displayNodes.includes(nodeData.name)) {
            // Store original onNodeCreated if it exists
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                // Call original if it exists
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                
                // Create display widget based on node type
                if (nodeData.name === "PromptDisplay") {
                    this.addCustomWidget(createPromptDisplayWidget(this));
                } else if (nodeData.name === "PromptDisplayLarge") {
                    this.addCustomWidget(createLargeDisplayWidget(this));
                } else if (nodeData.name === "PromptCompare") {
                    this.addCustomWidget(createCompareWidget(this));
                }
                
                // Set up serialization
                this.onSerialize = function(o) {
                    if (this.widgets_values) {
                        o.widgets_values = this.widgets_values;
                    }
                };
            };
            
            // Handle execution results
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                if (onExecuted) {
                    onExecuted.apply(this, arguments);
                }
                
                // Update display with results
                if (message && message.text) {
                    const widget = this.widgets?.find(w => w.name === "display");
                    if (widget) {
                        widget.value = Array.isArray(message.text) ? message.text[0] : message.text;
                    }
                }
                
                // Update info if available
                if (message && message.info) {
                    const infoWidget = this.widgets?.find(w => w.name === "info");
                    if (infoWidget) {
                        infoWidget.value = Array.isArray(message.info) ? message.info[0] : message.info;
                    }
                }
            };
        }
    }
});

/**
 * Create basic prompt display widget
 */
function createPromptDisplayWidget(node) {
    const widget = {
        type: "customtext",
        name: "display",
        get value() {
            return this._value || "";
        },
        set value(x) {
            this._value = x;
            this.inputEl?.setValue(x);
        },
        draw: function(ctx, node, widgetWidth, widgetY, widgetHeight) {
            // Draw background
            ctx.fillStyle = "#1a1a1a";
            ctx.fillRect(0, widgetY, widgetWidth, widgetHeight);
            
            // Draw border
            ctx.strokeStyle = "#444";
            ctx.strokeRect(0, widgetY, widgetWidth, widgetHeight);
            
            // Draw text
            ctx.fillStyle = "#ddd";
            ctx.font = "12px monospace";
            
            const padding = 10;
            const lineHeight = 16;
            const text = this.value || "No prompt to display";
            const lines = text.split('\n');
            
            let y = widgetY + padding + lineHeight;
            for (let i = 0; i < lines.length && y < widgetY + widgetHeight - padding; i++) {
                // Wrap long lines
                const wrappedLines = wrapText(ctx, lines[i], widgetWidth - padding * 2);
                for (const line of wrappedLines) {
                    if (y < widgetY + widgetHeight - padding) {
                        ctx.fillText(line, padding, y);
                        y += lineHeight;
                    }
                }
            }
        },
        computeSize: function(width) {
            const lineCount = (this.value || "").split('\n').length;
            return [width, Math.max(100, Math.min(400, lineCount * 16 + 20))];
        },
        serializeValue: function() {
            return this.value;
        }
    };
    
    node.addCustomWidget(widget);
    return widget;
}

/**
 * Create large display widget with adjustable size
 */
function createLargeDisplayWidget(node) {
    const widget = {
        type: "customtext_large",
        name: "display",
        get value() {
            return this._value || "";
        },
        set value(x) {
            this._value = x;
            this.inputEl?.setValue(x);
        },
        draw: function(ctx, node, widgetWidth, widgetY, widgetHeight) {
            // Get size from node properties
            const width = node.properties?.width || 512;
            const height = node.properties?.height || 256;
            
            // Draw background with subtle gradient
            const gradient = ctx.createLinearGradient(0, widgetY, 0, widgetY + height);
            gradient.addColorStop(0, "#1e1e1e");
            gradient.addColorStop(1, "#161616");
            ctx.fillStyle = gradient;
            ctx.fillRect(0, widgetY, width, height);
            
            // Draw border with glow effect
            ctx.strokeStyle = "#555";
            ctx.lineWidth = 1;
            ctx.strokeRect(0, widgetY, width, height);
            
            // Draw title bar
            ctx.fillStyle = "#2a2a2a";
            ctx.fillRect(0, widgetY, width, 25);
            
            // Draw title
            const title = node.properties?.title || "Prompt Display";
            ctx.fillStyle = "#fff";
            ctx.font = "bold 12px sans-serif";
            ctx.fillText(title, 10, widgetY + 17);
            
            // Draw info (word count, etc.)
            if (this.info) {
                ctx.fillStyle = "#888";
                ctx.font = "10px sans-serif";
                ctx.textAlign = "right";
                ctx.fillText(this.info, width - 10, widgetY + 17);
                ctx.textAlign = "left";
            }
            
            // Draw text content
            ctx.fillStyle = "#e0e0e0";
            ctx.font = "13px 'Courier New', monospace";
            
            const padding = 10;
            const lineHeight = 18;
            const text = this.value || "No prompt to display";
            const lines = text.split('\n');
            
            // Create clipping region for text area
            ctx.save();
            ctx.beginPath();
            ctx.rect(padding, widgetY + 30, width - padding * 2, height - 35);
            ctx.clip();
            
            let y = widgetY + 45;
            for (const line of lines) {
                const wrappedLines = wrapText(ctx, line, width - padding * 2);
                for (const wrappedLine of wrappedLines) {
                    ctx.fillText(wrappedLine, padding, y);
                    y += lineHeight;
                }
            }
            
            ctx.restore();
        },
        computeSize: function(width) {
            const height = node.properties?.height || 256;
            return [node.properties?.width || width, height];
        },
        info: "",
        serializeValue: function() {
            return this.value;
        }
    };
    
    node.addCustomWidget(widget);
    return widget;
}

/**
 * Create comparison widget for two prompts
 */
function createCompareWidget(node) {
    const widget = {
        type: "customcompare",
        name: "compare_display",
        promptA: "",
        promptB: "",
        comparison: "",
        draw: function(ctx, node, widgetWidth, widgetY, widgetHeight) {
            const halfWidth = widgetWidth / 2 - 5;
            const height = widgetHeight;
            
            // Draw backgrounds
            ctx.fillStyle = "#1a1a1a";
            ctx.fillRect(0, widgetY, halfWidth, height);
            ctx.fillRect(halfWidth + 10, widgetY, halfWidth, height);
            
            // Draw borders
            ctx.strokeStyle = "#444";
            ctx.strokeRect(0, widgetY, halfWidth, height);
            ctx.strokeRect(halfWidth + 10, widgetY, halfWidth, height);
            
            // Draw titles
            ctx.fillStyle = "#2a2a2a";
            ctx.fillRect(0, widgetY, halfWidth, 20);
            ctx.fillRect(halfWidth + 10, widgetY, halfWidth, 20);
            
            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            ctx.fillText(node.properties?.title_a || "Original", 5, widgetY + 14);
            ctx.fillText(node.properties?.title_b || "Optimized", halfWidth + 15, widgetY + 14);
            
            // Draw prompts
            ctx.fillStyle = "#ddd";
            ctx.font = "11px monospace";
            
            const padding = 5;
            const lineHeight = 14;
            
            // Draw prompt A
            drawTextInBox(ctx, this.promptA, 0, widgetY + 25, halfWidth, height - 30, padding, lineHeight);
            
            // Draw prompt B
            drawTextInBox(ctx, this.promptB, halfWidth + 10, widgetY + 25, halfWidth, height - 30, padding, lineHeight);
            
            // Draw comparison info at bottom if available
            if (this.comparison) {
                ctx.fillStyle = "#333";
                ctx.fillRect(0, widgetY + height - 40, widgetWidth, 40);
                ctx.fillStyle = "#aaa";
                ctx.font = "10px sans-serif";
                
                const compLines = this.comparison.split('\n');
                let y = widgetY + height - 30;
                for (const line of compLines) {
                    ctx.fillText(line, 10, y);
                    y += 12;
                }
            }
        },
        computeSize: function(width) {
            return [width, 350];
        },
        serializeValue: function() {
            return {
                promptA: this.promptA,
                promptB: this.promptB,
                comparison: this.comparison
            };
        }
    };
    
    node.addCustomWidget(widget);
    return widget;
}

/**
 * Helper function to wrap text to fit width
 */
function wrapText(ctx, text, maxWidth) {
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';
    
    for (const word of words) {
        const testLine = currentLine ? currentLine + ' ' + word : word;
        const metrics = ctx.measureText(testLine);
        
        if (metrics.width > maxWidth && currentLine) {
            lines.push(currentLine);
            currentLine = word;
        } else {
            currentLine = testLine;
        }
    }
    
    if (currentLine) {
        lines.push(currentLine);
    }
    
    return lines.length ? lines : [''];
}

/**
 * Helper function to draw text in a box with clipping
 */
function drawTextInBox(ctx, text, x, y, width, height, padding, lineHeight) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(x, y, width, height);
    ctx.clip();
    
    const lines = text.split('\n');
    let currentY = y + padding + lineHeight;
    
    for (const line of lines) {
        if (currentY > y + height - padding) break;
        
        const wrappedLines = wrapText(ctx, line, width - padding * 2);
        for (const wrappedLine of wrappedLines) {
            if (currentY > y + height - padding) break;
            ctx.fillText(wrappedLine, x + padding, currentY);
            currentY += lineHeight;
        }
    }
    
    ctx.restore();
}

// Export for use in other modules
export { createPromptDisplayWidget, createLargeDisplayWidget, createCompareWidget };