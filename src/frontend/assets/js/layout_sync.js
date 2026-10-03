(function() {
    window.scalarisLayout = {
        emit: function(reason) {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setTimeout(() => {
                        document.dispatchEvent(new CustomEvent('scalaris:layout', { detail: { reason } }));
                    }, 120);
                });
            });
        }
    };

    // Plotly sync
    let resizeTimeout;
    function resizePlots() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const plots = document.querySelectorAll('.js-plotly-plot');
            plots.forEach(plot => {
                if (plot.isConnected && window.Plotly) {
                    try {
                        const isGL3D = plot._fullLayout && plot._fullLayout._has && plot._fullLayout._has('gl3d');
                        if (isGL3D) {
                            // Delay slightly more for GL3D to ensure transition finished
                            setTimeout(() => {
                                if (plot.isConnected) Plotly.Plots.resize(plot);
                            }, 250);
                        } else {
                            Plotly.Plots.resize(plot);
                        }
                    } catch (e) {}
                }
            });
        }, 120);
    }

    document.addEventListener('scalaris:layout', resizePlots);
    document.addEventListener('scalaris:glosa', resizePlots);

    // ResizeObserver per plot
    const ro = new ResizeObserver((entries) => {
        let shouldResize = false;
        for (let entry of entries) {
            if (entry.target.classList.contains('js-plotly-plot')) {
                shouldResize = true;
                break;
            }
        }
        if (shouldResize) resizePlots();
    });

    let scanPending = false;
    function scanPlots() {
        document.querySelectorAll('.js-plotly-plot').forEach(plot => {
            ro.observe(plot);
        });
        scanPending = false;
    }

    const mo = new MutationObserver((mutations) => {
        let hasNewNodes = false;
        for (let mut of mutations) {
            if (mut.addedNodes.length > 0) {
                hasNewNodes = true;
                break;
            }
        }
        if (hasNewNodes && !scanPending) {
            scanPending = true;
            requestAnimationFrame(scanPlots);
        }
    });

    mo.observe(document.documentElement, { childList: true, subtree: true });
    document.addEventListener('DOMContentLoaded', scanPlots);
    scanPlots(); // Initial scan
})();
