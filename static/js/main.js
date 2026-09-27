document.addEventListener('DOMContentLoaded', () => {
    loadBoard();
    document.getElementById('applyForm').addEventListener('submit', handleFormSubmit);
});

async function loadBoard() {
    const response = await fetch('/api/candidates');
    const candidates = await response.json();
    
    document.querySelectorAll('.card-holder').forEach(el => el.innerHTML = '');
    
    candidates.forEach(cand => {
        const column = document.getElementById(cand.stage).querySelector('.card-holder');
        const card = document.createElement('div');
        card.className = 'candidate-card';
        card.id = cand.id;
        card.draggable = true;
        card.addEventListener('dragstart', dragStart);

        card.innerHTML = `
            <div><strong>🥷 ${cand.id}</strong></div>
            <div style="font-size:0.85rem; color:#94a3b8; margin: 5px 0;">Exp: ${cand.experience}</div>
            <div class="skills-list">
                ${cand.skills.map(function(s) { return '<span class="tag">' + s + '</span>'; }).join(' ')}
            </div>
            <div class="score-badge">Match: ${cand.fit_score}%</div>
        `;
        column.appendChild(card);
    });
    updateCounts();
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const experience = document.getElementById('experience').value;
    const skills = document.getElementById('skills').value;
    
    const response = await fetch('/api/candidates/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ experience, skills })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
        alert(`Application Logged! Your Profile ID is ${result.candidate.id}.\nCalculated Keyword Match Rating: ${result.fit_score}%`);
        document.getElementById('applyForm').reset();
        loadBoard();
    }
}

function dragStart(e) { 
    e.dataTransfer.setData('text/plain', e.target.id); 
}

function allowDrop(e) { 
    e.preventDefault(); 
}

async function drop(e, stageName) {
    e.preventDefault();
    const candidateId = e.dataTransfer.getData('text/plain');
    const movedElement = document.getElementById(candidateId);
    if (!movedElement) return;

    // STAGING GATE RULE: Enforce the 50% match requirement for the Interview Stage
    if (stageName === 'interview') {
        const scoreBadgeText = movedElement.querySelector('.score-badge').innerText;
        const matchScore = parseInt(scoreBadgeText.replace(/[^0-9]/g, ''), 10);

        if (matchScore < 50) {
            alert(`⚠️ Gate Blocked: This profile has a Match Score of ${matchScore}%. Profiles require at least 50% matching keywords to move to the Interview stage.`);
            return;
        }
    }
    
    const targetHolder = document.getElementById(stageName).querySelector('.card-holder');
    targetHolder.appendChild(movedElement);
    updateCounts();

    await fetch('/api/candidates/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: candidateId, stage: stageName })
    });
}

function updateCounts() {
    document.querySelectorAll('.column').forEach(col => {
        const count = col.querySelector('.card-holder').children.length;
        col.querySelector('.count').innerText = count;
    });
}