// Tab Switching
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        tabButtons.forEach(btn => {
            btn.classList.remove('text-teal-600', 'border-teal-600');
            btn.classList.add('text-gray-600');
        });
        button.classList.add('text-teal-600', 'border-teal-600');
        button.classList.remove('text-gray-600');

        tabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(button.dataset.tab).classList.add('active');
    });
});

// Search and Highlight
function highlightText(text, query) {
    if (!query) return { highlighted: text, count: 0 };
    const regex = new RegExp(`(${query})`, 'gi');
    const matches = text.match(regex) || [];
    return {
        highlighted: text.replace(regex, '<span class="bg-amber-200">$1</span>'),
        count: matches.length
    };
}

document.getElementById('search-button').addEventListener('click', () => {
    const query = document.getElementById('search-query').value;
    const documentText = document.getElementById('document-text');
    const originalText = documentText.innerText || documentText.textContent;
    const { highlighted, count } = highlightText(originalText, query);
    documentText.innerHTML = highlighted;
    document.getElementById('search-results').textContent = count > 0 ? `Found ${count} matches` : 'No matches found';
    if (count > 0) {
        document.querySelector('.bg-amber-200').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});

document.getElementById('clear-highlights').addEventListener('click', () => {
    const documentText = document.getElementById('document-text');
    documentText.innerHTML = documentText.innerText || documentText.textContent;
    document.getElementById('search-results').textContent = '';
});

// Explain Selected Text
const explainButton = document.getElementById('explain-button');
const explanationResult = document.getElementById('explanation-result');
let selectedText = '';

document.addEventListener('selectionchange', () => {
    selectedText = window.getSelection().toString().trim();
    explainButton.disabled = !selectedText;
});

explainButton.addEventListener('click', async () => {
    if (!selectedText) return;

    explainButton.disabled = true;
    explainButton.innerHTML = `
        <svg class="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
    `;
    explanationResult.innerHTML = '';

    try {
        const response = await fetch('/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: selectedText }),
        });
        const data = await response.json();
        explanationResult.innerHTML = data.explanation || 'No explanation generated.';
        explanationResult.classList.remove('hidden');
        explanationResult.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        explanationResult.innerHTML = 'Error: Could not fetch explanation.';
        explanationResult.classList.remove('hidden');
        console.error('Fetch error:', error);
    } finally {
        explainButton.disabled = false;
        explainButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        `;
    }
});

// Form Submission Loading State for Q&A
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
        `;
    });
});