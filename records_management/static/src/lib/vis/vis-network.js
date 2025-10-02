/* Placeholder local vis-network JS.
 * Replace this file with the unminified vis-network distribution (version 9.1.6 recommended).
 * The dynamic loader checks for window.vis && window.vis.Network after injecting this script.
 */
(function(){
    window.vis = window.vis || {};
    // Lightweight stub so dependent code does not crash if full library not yet installed.
    if(!window.vis.Network) {
        window.vis.Network = function(container, data, options){
            console.warn('[vis-network placeholder] Full library not installed. Graph rendering skipped.');
            this.container = container; this.data = data; this.options = options;
        };
    }
})();
