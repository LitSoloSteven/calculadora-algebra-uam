(function() {
    window.scalarisGlosa = {
        mode: () => getComputedStyle(document.documentElement).getPropertyValue('--glosa-mode').trim() || 'push',
        isOpen: () => document.documentElement.getAttribute('data-glosa') === 'open',
        open: (opts={}) => setGlosaState('open', opts),
        close: (opts={}) => setGlosaState('closed', opts),
        toggle: (opts={}) => setGlosaState(window.scalarisGlosa.isOpen() ? 'closed' : 'open', opts)
    };

    function setGlosaState(newState, opts) {
        if (newState === (window.scalarisGlosa.isOpen() ? 'open' : 'closed')) return;

        const html = document.documentElement;
        const mode = window.scalarisGlosa.mode();
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const instant = opts.instant || prefersReducedMotion;

        performance.mark('glosa:toggle:start');

        // Measure FLIP targets
        const viewRoot = document.querySelector('.view-root');
        const viewRootWidthBefore = viewRoot ? viewRoot.getBoundingClientRect().width : 0;
        
        const flipTargets = document.querySelectorAll('.view-root, .crumbs, .q-header .panel-card');
        const flipBefore = new Map();
        flipTargets.forEach(el => flipBefore.set(el, el.getBoundingClientRect()));

        // Apply state
        if (instant) {
            html.setAttribute('data-glosa-instant', '');
        }
        
        html.setAttribute('data-glosa', newState);
        
        if (mode === 'push') {
            try { localStorage.setItem('scalaris:glosa', newState); } catch(e) {}
        }

        // Measure after
        const viewRootWidthAfter = viewRoot ? viewRoot.getBoundingClientRect().width : 0;
        
        if (!instant && viewRootWidthBefore === viewRootWidthAfter && mode === 'push') {
            // FLIP only translateX
            const dur = parseFloat(getComputedStyle(html).getPropertyValue('--dur-med')) || 240;
            const ease = getComputedStyle(html).getPropertyValue('--ease-std') || 'cubic-bezier(0.32, 0.72, 0, 1)';
            
            flipTargets.forEach(el => {
                const before = flipBefore.get(el);
                const after = el.getBoundingClientRect();
                const dx = before.left - after.left;
                if (dx !== 0) {
                    el.animate([
                        { transform: `translateX(${dx}px)` },
                        { transform: 'translateX(0)' }
                    ], {
                        duration: dur,
                        easing: ease
                    });
                }
            });
        } else if (mode === 'push' && viewRootWidthBefore !== viewRootWidthAfter) {
            // Reflow happened
            if (window.scalarisLayout) {
                window.scalarisLayout.emit('dock');
            }
        }

        // Manage Focus and attributes
        const dock = document.getElementById('glosa-dock');
        if (dock) {
            dock.inert = newState === 'closed';
            dock.setAttribute('aria-expanded', newState === 'open');
            if (mode !== 'push') {
                dock.setAttribute('role', 'dialog');
                dock.setAttribute('aria-modal', 'true');
            } else {
                dock.setAttribute('role', 'complementary');
                dock.removeAttribute('aria-modal');
            }
        }

        // Manage traps
        if (mode !== 'push') {
            const siblings = Array.from(document.body.children).filter(el => 
                el !== dock && !el.hasAttribute('data-glosa-keep') && el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && !el.classList.contains('glosa-scrim') && !el.classList.contains('glosa-fab') && !el.classList.contains('glosa-dock')
            );
            const header = document.querySelector('.q-header');
            if (newState === 'open') {
                siblings.forEach(el => { if (!el.inert) { el.setAttribute('data-glosa-inert', ''); el.inert = true; } });
                if (header) header.inert = true;
            } else {
                document.querySelectorAll('[data-glosa-inert]').forEach(el => { el.removeAttribute('data-glosa-inert'); el.inert = false; });
                if (header) header.inert = false;
            }
        }

        if (newState === 'open') {
            if (mode === 'sheet') {
                history.pushState({glosa: true}, '');
            }
            if (window.matchMedia('(pointer: fine)').matches || opts.trigger === 'keyboard') {
                const input = dock ? dock.querySelector('.glosa-input textarea') : null;
                if (input) setTimeout(() => input.focus(), 50);
            } else {
                if (dock) setTimeout(() => dock.focus(), 50);
            }
        } else {
            if (opts.triggerEl) {
                setTimeout(() => opts.triggerEl.focus(), 50);
            } else {
                const fab = document.querySelector('.glosa-fab');
                if (fab) setTimeout(() => fab.focus(), 50);
            }
        }

        if (instant) {
            // Force reflow and remove transistory attribute
            void document.body.offsetHeight;
            requestAnimationFrame(() => {
                html.removeAttribute('data-glosa-instant');
            });
        }
        
        performance.mark('glosa:toggle:end');
        performance.measure('glosa:toggle', 'glosa:toggle:start', 'glosa:toggle:end');
        
        document.dispatchEvent(new CustomEvent('scalaris:glosa', {
            detail: { open: newState === 'open', mode }
        }));
    }

    // Observers and event listeners
    document.addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('[data-glosa-toggle]');
        if (toggleBtn) {
            const triggerType = e.detail === 0 ? 'keyboard' : 'mouse';
            window.scalarisGlosa.toggle({ trigger: triggerType, instant: e.detail === 0, triggerEl: toggleBtn });
            return;
        }
        
        const closeBtn = e.target.closest('[data-glosa-close]');
        if (closeBtn) {
            const triggerType = e.detail === 0 ? 'keyboard' : 'mouse';
            window.scalarisGlosa.close({ trigger: triggerType, instant: e.detail === 0, triggerEl: closeBtn });
            if (window.scalarisGlosa.mode() === 'sheet' && history.state && history.state.glosa) {
                history.back();
            }
            return;
        }
        
        if (e.target.closest('.glosa-scrim')) {
            window.scalarisGlosa.close();
            if (window.scalarisGlosa.mode() === 'sheet' && history.state && history.state.glosa) {
                history.back();
            }
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !e.defaultPrevented) {
            const dock = document.getElementById('glosa-dock');
            const inDock = dock && dock.contains(e.target);
            if (inDock || window.scalarisGlosa.mode() !== 'push') {
                window.scalarisGlosa.close({ instant: true, trigger: 'keyboard' });
                if (window.scalarisGlosa.mode() === 'sheet' && history.state && history.state.glosa) {
                    history.back();
                }
            }
        }
    });

    window.addEventListener('popstate', (e) => {
        if (window.scalarisGlosa.mode() === 'sheet' && window.scalarisGlosa.isOpen()) {
            if (!e.state || !e.state.glosa) {
                window.scalarisGlosa.close();
            }
        }
    });

    // visualViewport resize for sheet mode keyboard avoidance
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', () => {
            if (window.scalarisGlosa.isOpen() && window.scalarisGlosa.mode() === 'sheet') {
                const kbHeight = window.innerHeight - window.visualViewport.height;
                document.documentElement.style.setProperty('--glosa-kb', Math.max(0, kbHeight) + 'px');
            }
        });
        window.visualViewport.addEventListener('scroll', () => {
            if (window.scalarisGlosa.isOpen() && window.scalarisGlosa.mode() === 'sheet') {
                const kbHeight = window.innerHeight - window.visualViewport.height;
                document.documentElement.style.setProperty('--glosa-kb', Math.max(0, kbHeight) + 'px');
            }
        });
    }
    
    // mode change
    let lastMode = window.scalarisGlosa.mode();
    window.addEventListener('resize', () => {
        const newMode = window.scalarisGlosa.mode();
        if (newMode !== lastMode) {
            if (window.scalarisGlosa.isOpen()) {
                if (newMode !== 'push') {
                    window.scalarisGlosa.close({instant: true});
                }
            }
            lastMode = newMode;
        }
    });

    // Mount observer
    const observer = new MutationObserver((mutations, obs) => {
        const dock = document.getElementById('glosa-dock');
        if (dock) {
            document.documentElement.setAttribute('data-glosa-ready', '');
            dock.inert = !window.scalarisGlosa.isOpen();
            dock.setAttribute('aria-expanded', window.scalarisGlosa.isOpen());
            obs.disconnect();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

})();
