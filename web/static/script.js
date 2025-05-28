document.addEventListener('DOMContentLoaded', () => {
    const naturalCommandTextarea = document.getElementById('natural-command');
    const processCommandButton = document.getElementById('process-command-button');
    
    const reviewSection = document.getElementById('review-section');
    const reviewArea = document.getElementById('review-area');
    const generatedCodeArea = document.getElementById('generated-code-area');
    const executeBlenderButton = document.getElementById('execute-blender-button');

    const executionResultSection = document.getElementById('execution-result-section');
    const outputArea = document.getElementById('output-area');

    let currentGeneratedCode = ''; // Store the code to be executed

    processCommandButton.addEventListener('click', async () => {
        const command = naturalCommandTextarea.value;
        if (!command.trim()) {
            reviewArea.textContent = 'Please enter a command for Blender.';
            reviewArea.className = 'error';
            reviewSection.style.display = 'block';
            generatedCodeArea.textContent = '';
            executeBlenderButton.style.display = 'none';
            executionResultSection.style.display = 'none';
            return;
        }

        reviewArea.textContent = 'Processing your command...';
        reviewArea.className = '';
        generatedCodeArea.textContent = '...';
        reviewSection.style.display = 'block';
        executeBlenderButton.style.display = 'none';
        executionResultSection.style.display = 'none';

        try {
            const response = await fetch('/api/blender/interpret', { // New endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ natural_language_command: command }),
            });

            const result = await response.json();

            if (response.ok) {
                reviewArea.textContent = result.review || 'No review provided.';
                generatedCodeArea.textContent = result.generated_code || '# No code generated.';
                currentGeneratedCode = result.generated_code || '';
                
                if (currentGeneratedCode && result.status === 'success') {
                    executeBlenderButton.style.display = 'block';
                    reviewArea.className = 'success'; 
                } else {
                    executeBlenderButton.style.display = 'none';
                    reviewArea.className = result.status === 'success' ? 'success' : 'error'; 
                }
            } else {
                reviewArea.textContent = `Error processing command: ${result.detail || response.statusText}`;
                reviewArea.className = 'error';
                generatedCodeArea.textContent = '# Error during interpretation.';
                executeBlenderButton.style.display = 'none';
            }
        } catch (error) {
            console.error('Error during interpretation request:', error);
            reviewArea.textContent = `Network or communication error: ${error.message}`;
            reviewArea.className = 'error';
            generatedCodeArea.textContent = '# Network error.';
            executeBlenderButton.style.display = 'none';
        }
    });

    executeBlenderButton.addEventListener('click', async () => {
        if (!currentGeneratedCode.trim()) {
            outputArea.textContent = 'No Blender code to execute.';
            outputArea.className = 'error';
            executionResultSection.style.display = 'block';
            return;
        }

        outputArea.textContent = 'Executing in Blender...';
        outputArea.className = '';
        executionResultSection.style.display = 'block';

        try {
            // Using the existing execute endpoint for the generated code
            const response = await fetch('/api/blender/execute', { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code: currentGeneratedCode }), // Send the generated code
            });

            const result = await response.json();

            if (response.ok) {
                let outputText = `Status: ${result.status}\n`;
                if (result.message) {
                    outputText += `Message: ${result.message}\n`;
                }
                // The actual print output from Blender script is in result.result
                if (result.result && result.result.trim()) {
                    outputText += `\nOutput Log:\n${result.result.trim()}`;
                } else if (result.status === 'success' && (!result.result || !result.result.trim())) {
                    outputText += `(No specific output log from script, but execution was successful)`
                }
                if (result.traceback) {
                    outputText += `\nTraceback:\n${result.traceback}`;
                }
                outputArea.textContent = outputText;
                outputArea.className = result.status === 'success' ? 'success' : 'error';
            } else {
                outputArea.textContent = `Error executing in Blender: ${result.detail || response.statusText}`;
                outputArea.className = 'error';
            }
        } catch (error) {
            console.error('Error during execution request:', error);
            outputArea.textContent = `Network or communication error during execution: ${error.message}`;
            outputArea.className = 'error';
        }
    });
}); 