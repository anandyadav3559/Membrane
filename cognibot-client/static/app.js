document.addEventListener('DOMContentLoaded', () => {
    const activeBlocksContainer = document.getElementById('activeBlocksContainer');
    const inactiveBlocksContainer = document.getElementById('inactiveBlocksContainer');
    const addBlockBtn = document.getElementById('addBlockBtn');
    const previewBtn = document.getElementById('previewBtn');
    const viewTrashBtn = document.getElementById('viewTrashBtn');
    
    // Modal Elements
    const modalOverlay = document.getElementById('modalOverlay');
    const modalTitle = document.getElementById('modalTitle');
    const modalLabel = document.getElementById('modalLabel');
    const modalInput = document.getElementById('modalInput');
    const modalForm = document.getElementById('modalForm');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelModalBtn = document.getElementById('cancelModalBtn');

    // Preview Elements
    const previewOverlay = document.getElementById('previewOverlay');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    const previewText = document.getElementById('previewText');
    const previewTokens = document.getElementById('previewTokens');
    const previewChars = document.getElementById('previewChars');
    const previewMapping = document.getElementById('previewMapping');

    // Trash Elements
    const trashOverlay = document.getElementById('trashOverlay');
    const closeTrashBtn = document.getElementById('closeTrashBtn');
    const trashBlocksContainer = document.getElementById('trashBlocksContainer');
    const trashChunksContainer = document.getElementById('trashChunksContainer');

    // State
    let currentModalAction = null; 
    let currentContextData = [];

    // Initialize block-level Sortables
    Sortable.create(activeBlocksContainer, {
        group: 'blocks',
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        onAdd: function (evt) {
            const blockId = evt.item.dataset.blockId;
            toggleBlock(blockId, true);
        }
    });

    Sortable.create(inactiveBlocksContainer, {
        group: 'blocks',
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        onAdd: function (evt) {
            const blockId = evt.item.dataset.blockId;
            toggleBlock(blockId, false);
        }
    });

    // Fetch and render initial data
    fetchContext();

    async function fetchContext() {
        try {
            const res = await fetch('/api/context');
            const data = await res.json();
            currentContextData = data.blocks || [];
            renderBlocks(currentContextData);
        } catch (error) {
            console.error('Error fetching context:', error);
        }
    }

    function renderBlocks(blocks) {
        activeBlocksContainer.innerHTML = '';
        inactiveBlocksContainer.innerHTML = '';

        let activeCount = 0;
        let inactiveCount = 0;
        
        // Split and sort blocks
        const activeBlocks = [];
        const inactiveBlocks = [];

        blocks.forEach(block => {
            const activeChunks = block.chunks.filter(c => c.is_active);
            const inactiveChunks = block.chunks.filter(c => !c.is_active);
            
            if (block.is_active) {
                activeBlocks.push({ block, chunks: activeChunks });
            }
            if (!block.is_active || inactiveChunks.length > 0) {
                inactiveBlocks.push({ block, chunks: inactiveChunks, isPartial: block.is_active });
            }
        });

        // Sort active blocks by their position in active_context.json
        activeBlocks.sort((a, b) => a.block.active_index - b.block.active_index);
        
        // Sort inactive blocks by newest first (timestamp)
        inactiveBlocks.sort((a, b) => b.block.timestamp - a.block.timestamp);

        activeBlocks.forEach(item => {
            activeCount++;
            const el = createBlockElement(item.block, item.chunks, true);
            activeBlocksContainer.appendChild(el);
        });

        inactiveBlocks.forEach(item => {
            if (!item.block.is_active) inactiveCount++;
            const el = createBlockElement(item.block, item.chunks, false, item.isPartial);
            inactiveBlocksContainer.appendChild(el);
        });

        if (activeBlocksContainer.children.length === 0) {
            activeBlocksContainer.innerHTML = '<div class="empty-state">Drag blocks or chunks here to activate them.</div>';
        }
        if (inactiveBlocksContainer.children.length === 0) {
            inactiveBlocksContainer.innerHTML = '<div class="empty-state">No available blocks. Add a new block!</div>';
        }

        document.getElementById('activeBadge').textContent = activeCount;
        document.getElementById('inactiveBadge').textContent = inactiveCount;

        // Initialize Chunk Sortables
        document.querySelectorAll('.chunks-container').forEach(container => {
            Sortable.create(container, {
                group: 'chunks',
                animation: 150,
                ghostClass: 'sortable-ghost',
                onAdd: function (evt) {
                    const chunkId = evt.item.dataset.chunkId;
                    const originalBlockId = evt.item.dataset.blockId;
                    const targetBlockId = evt.to.dataset.blockId;
                    const isDroppingToActive = evt.to.closest('.pane-active') !== null;
                    
                    if (originalBlockId !== targetBlockId) {
                        moveChunk(originalBlockId, targetBlockId, chunkId, isDroppingToActive);
                    } else {
                        toggleChunk(originalBlockId, chunkId, isDroppingToActive);
                    }
                }
            });
        });
    }

    function createBlockElement(block, chunksToRender, isActivePane, isPartial = false) {
        const card = document.createElement('div');
        card.className = `block-card`;
        card.dataset.blockId = block.block_id;
        
        // If it's the inactive pane but the block is already active (we're just showing leftover inactive chunks)
        // Disable dragging the whole block to avoid confusion, only allow chunk dragging.
        const canDragBlock = !(isActivePane === false && isPartial);
        
        const date = new Date(block.timestamp * 1000).toLocaleString();

        let chunksHtml = '';
        if (chunksToRender.length > 0) {
            chunksHtml = chunksToRender.map(chunk => `
                <div class="chunk-item" data-block-id="${block.block_id}" data-chunk-id="${chunk.chunk_id}" onclick="toggleChunkClick(event, '${block.block_id}', '${chunk.chunk_id}', ${!chunk.is_active})" style="cursor: pointer;">
                    <div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>
                    <div class="chunk-content">${escapeHTML(chunk.content)}</div>
                    <div class="chunk-actions">
                        <button class="icon-btn" onclick="openEditChunkModal('${block.block_id}', '${chunk.chunk_id}', \`${escapeJS(chunk.content)}\`)">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="icon-btn danger" onclick="deleteChunk('${block.block_id}', '${chunk.chunk_id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }

        card.innerHTML = `
            <div class="block-header" onclick="toggleBlockClick(event, '${block.block_id}', ${!isActivePane})" style="cursor: pointer;">
                ${canDragBlock ? '<div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>' : '<div style="width: 24px;"></div>'}
                <div style="flex-grow: 1;">
                    <div class="block-prompt">${escapeHTML(block.user_prompt)}</div>
                    <div class="block-meta">ID: ${block.block_id} • ${date}</div>
                </div>
                <div class="block-actions">
                    <button class="icon-btn" onclick="openEditBlockModal('${block.block_id}', \`${escapeJS(block.user_prompt)}\`)">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="icon-btn danger" onclick="deleteBlock('${block.block_id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="chunks-container" data-block-id="${block.block_id}">
                ${chunksHtml}
            </div>
            <button class="btn btn-secondary" style="align-self: flex-start; margin-top: 0.5rem; font-size: 0.75rem; padding: 0.4rem 0.8rem;" onclick="openAddChunkModal('${block.block_id}')">
                <i class="fas fa-plus"></i> Add Chunk
            </button>
        `;
        return card;
    }

    // Modal Logic
    addBlockBtn.addEventListener('click', () => {
        currentModalAction = { type: 'add_block' };
        modalTitle.textContent = 'Add New Block';
        modalLabel.textContent = 'User Prompt';
        modalInput.value = '';
        openModal(modalOverlay);
    });

    window.openEditBlockModal = (blockId, prompt) => {
        currentModalAction = { type: 'edit_block', blockId };
        modalTitle.textContent = 'Edit Block';
        modalLabel.textContent = 'User Prompt';
        modalInput.value = unescapeJS(prompt);
        openModal(modalOverlay);
    };

    window.openAddChunkModal = (blockId) => {
        currentModalAction = { type: 'add_chunk', blockId };
        modalTitle.textContent = 'Add New Chunk';
        modalLabel.textContent = 'Chunk Content';
        modalInput.value = '';
        openModal(modalOverlay);
    };

    window.openEditChunkModal = (blockId, chunkId, content) => {
        currentModalAction = { type: 'edit_chunk', blockId, chunkId };
        modalTitle.textContent = 'Edit Chunk';
        modalLabel.textContent = 'Chunk Content';
        modalInput.value = unescapeJS(content);
        openModal(modalOverlay);
    };

    function openModal(overlay) {
        overlay.classList.remove('hidden');
        if (overlay === modalOverlay) {
            setTimeout(() => modalInput.focus(), 100);
        }
    }

    function closeModal(overlay) {
        overlay.classList.add('hidden');
    }

    closeModalBtn.addEventListener('click', () => closeModal(modalOverlay));
    cancelModalBtn.addEventListener('click', () => closeModal(modalOverlay));
    closePreviewBtn.addEventListener('click', () => closeModal(previewOverlay));
    closeTrashBtn.addEventListener('click', () => closeModal(trashOverlay));
    
    viewTrashBtn.addEventListener('click', () => {
        fetchTrash();
        openModal(trashOverlay);
    });
    
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal(overlay);
        });
    });

    modalForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const value = modalInput.value.trim();
        if (!value) return;

        try {
            if (currentModalAction.type === 'add_block') {
                await fetch('/api/blocks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_prompt: value })
                });
            } else if (currentModalAction.type === 'edit_block') {
                await fetch(`/api/blocks/${currentModalAction.blockId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_prompt: value })
                });
            } else if (currentModalAction.type === 'add_chunk') {
                await fetch(`/api/blocks/${currentModalAction.blockId}/chunks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: value })
                });
            } else if (currentModalAction.type === 'edit_chunk') {
                await fetch(`/api/blocks/${currentModalAction.blockId}/chunks/${currentModalAction.chunkId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: value })
                });
            }
            closeModal(modalOverlay);
            fetchContext();
        } catch (error) {
            console.error('Error saving:', error);
            alert('Failed to save. Check console.');
        }
    });

    // API Toggle logic called by drag and drop or click
    window.toggleBlockClick = (e, blockId, activate) => {
        if (e.target.closest('button') || e.target.closest('.drag-handle')) return;
        toggleBlock(blockId, activate);
    };

    window.toggleChunkClick = (e, blockId, chunkId, activate) => {
        if (e.target.closest('button') || e.target.closest('.drag-handle')) return;
        e.stopPropagation(); // prevent triggering block click if they are nested differently
        toggleChunk(blockId, chunkId, activate);
    };

    window.toggleBlock = async (blockId, activate) => {
        try {
            await fetch('/api/toggle-block', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ block_id: blockId, activate })
            });
            fetchContext(); 
        } catch (error) {
            console.error('Error toggling block:', error);
        }
    };

    window.toggleChunk = async (blockId, chunkId, activate) => {
        try {
            await fetch('/api/toggle-chunk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ block_id: blockId, chunk_id: chunkId, activate })
            });
            fetchContext();
        } catch (error) {
            console.error('Error toggling chunk:', error);
        }
    };

    window.moveChunk = async (sourceBlockId, targetBlockId, chunkId, activate) => {
        try {
            await fetch(`/api/blocks/${sourceBlockId}/chunks/${chunkId}/move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_block_id: targetBlockId, activate })
            });
            fetchContext();
        } catch (error) {
            console.error('Error moving chunk:', error);
        }
    };

    window.deleteBlock = async (blockId) => {
        if (!confirm('Are you sure you want to delete this block? It will be moved to trash.')) return;
        try {
            await fetch(`/api/blocks/${blockId}`, { method: 'DELETE' });
            fetchContext();
        } catch (error) {
            console.error('Error deleting block:', error);
        }
    };

    window.deleteChunk = async (blockId, chunkId) => {
        if (!confirm('Are you sure you want to delete this chunk? It will be moved to trash.')) return;
        try {
            await fetch(`/api/blocks/${blockId}/chunks/${chunkId}`, { method: 'DELETE' });
            fetchContext();
        } catch (error) {
            console.error('Error deleting chunk:', error);
        }
    };

    // Trash Logic
    async function fetchTrash() {
        try {
            const res = await fetch('/api/trash');
            const data = await res.json();
            renderTrash(data);
        } catch (error) {
            console.error('Error fetching trash:', error);
        }
    }

    function renderTrash(trashData) {
        trashBlocksContainer.innerHTML = '';
        trashChunksContainer.innerHTML = '';

        const blocks = trashData.blocks || [];
        const chunks = trashData.chunks || [];

        if (blocks.length === 0) {
            trashBlocksContainer.innerHTML = '<div class="empty-state">No deleted blocks.</div>';
        } else {
            blocks.forEach(block => {
                const date = new Date(block.deleted_at * 1000).toLocaleString();
                const card = document.createElement('div');
                card.className = 'block-card';
                card.innerHTML = `
                    <div class="block-header">
                        <div style="width: 24px;"></div>
                        <div style="flex-grow: 1;">
                            <div class="block-prompt">${escapeHTML(block.user_prompt)}</div>
                            <div class="block-meta">Deleted: ${date}</div>
                        </div>
                        <div class="block-actions">
                            <button class="icon-btn btn-primary" onclick="restoreBlock('${block.block_id}')" title="Restore Block">
                                <i class="fas fa-trash-restore"></i>
                            </button>
                        </div>
                    </div>
                `;
                trashBlocksContainer.appendChild(card);
            });
        }

        if (chunks.length === 0) {
            trashChunksContainer.innerHTML = '<div class="empty-state">No deleted chunks.</div>';
        } else {
            chunks.forEach(chunk => {
                const date = new Date(chunk.deleted_at * 1000).toLocaleString();
                const card = document.createElement('div');
                card.className = 'chunk-item';
                card.innerHTML = `
                    <div style="width: 24px;"></div>
                    <div class="chunk-content">
                        ${escapeHTML(chunk.content)}
                        <div class="block-meta" style="margin-top: 4px;">Deleted: ${date}</div>
                    </div>
                    <div class="chunk-actions">
                        <button class="icon-btn btn-primary" onclick="restoreChunk('${chunk.chunk_id}')" title="Restore Chunk">
                            <i class="fas fa-trash-restore"></i>
                        </button>
                    </div>
                `;
                trashChunksContainer.appendChild(card);
            });
        }
    }

    window.restoreBlock = async (blockId) => {
        try {
            await fetch(`/api/trash/restore-block/${blockId}`, { method: 'POST' });
            fetchTrash();
            fetchContext();
        } catch (error) {
            console.error('Error restoring block:', error);
        }
    };

    window.restoreChunk = async (chunkId) => {
        try {
            await fetch(`/api/trash/restore-chunk/${chunkId}`, { method: 'POST' });
            fetchTrash();
            fetchContext();
        } catch (error) {
            console.error('Error restoring chunk:', error);
        }
    };

    // Preview Logic
    previewBtn.addEventListener('click', () => {
        let concatenatedText = '';
        let mappings = [];
        
        currentContextData.forEach(block => {
            if (block.is_active) {
                const activeChunks = block.chunks.filter(c => c.is_active);
                if (activeChunks.length > 0) {
                    mappings.push(`Block: ${block.block_id} ("${block.user_prompt.substring(0, 30)}...")`);
                    activeChunks.forEach(chunk => {
                        concatenatedText += chunk.content + '\n\n';
                        mappings.push(`  ↳ Chunk: ${chunk.chunk_id}`);
                    });
                }
            }
        });

        const charCount = concatenatedText.length;
        // Simple token estimation (approx 4 chars per token)
        const tokenEstimate = Math.ceil(charCount / 4);

        previewText.value = concatenatedText.trim() || 'No active context available.';
        previewChars.textContent = charCount;
        previewTokens.textContent = tokenEstimate;
        previewMapping.textContent = mappings.join('\n') || 'No active blocks mapped.';

        openModal(previewOverlay);
    });

    // Utils
    function escapeHTML(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag]));
    }
    
    function escapeJS(str) {
        if (!str) return '';
        return str.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
    }
    
    function unescapeJS(str) {
        if (!str) return '';
        return str.replace(/\\\\/g, '\\').replace(/\\`/g, '`').replace(/\\\$/g, '$');
    }
});
