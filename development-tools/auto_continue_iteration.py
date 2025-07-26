#!/usr/bin/env python3
"""
Auto Continue Iteration Script
Automatically responds "yes" to iteration prompts and continues systematic field implementation
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime

class AutoIterationManager:
    def __init__(self):
        self.continue_iteration = True
        self.session_stats = {
            'models_completed': 0,
            'fields_implemented': 0,
            'start_time': datetime.now(),
            'errors_fixed': 0
        }
        
    def log_progress(self, message):
        """Log progress with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] AUTO-ITERATOR: {message}")
        
    def auto_respond_yes(self):
        """Automatically respond yes to iteration prompts"""
        while self.continue_iteration:
            time.sleep(0.5)  # Check every 500ms
            # This would intercept dialog prompts if they exist
            # For now, it serves as a placeholder for the automation logic
            
    def run_business_field_analysis(self):
        """Run the business field analysis and return results"""
        try:
            result = subprocess.run([
                'python3', 
                '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/development-tools/find_business_missing_fields.py'
            ], capture_output=True, text=True, cwd='/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.log_progress(f"Error running analysis: {result.stderr}")
                return None
        except Exception as e:
            self.log_progress(f"Exception running analysis: {e}")
            return None
            
    def extract_remaining_models(self, analysis_output):
        """Extract list of models that still need attention"""
        if not analysis_output:
            return []
            
        models = []
        lines = analysis_output.split('\n')
        for line in lines:
            if '🚨 Model:' in line:
                model_name = line.split('🚨 Model:')[1].strip()
                models.append(model_name)
        return models
        
    def extract_critical_fields_count(self, analysis_output):
        """Extract the total critical missing fields count"""
        if not analysis_output:
            return 0
            
        lines = analysis_output.split('\n')
        for line in lines:
            if '🎯 CRITICAL BUSINESS MISSING FIELDS:' in line:
                try:
                    count = int(line.split(':')[1].strip())
                    return count
                except:
                    pass
        return 0
        
    def start_auto_iteration(self):
        """Start the automatic iteration process"""
        self.log_progress("🚀 AUTO-ITERATION STARTED")
        self.log_progress("Will automatically continue iteration when prompted")
        self.log_progress("Press Ctrl+C to stop auto-iteration")
        
        # Start background thread for auto-responses
        response_thread = threading.Thread(target=self.auto_respond_yes, daemon=True)
        response_thread.start()
        
        try:
            iteration_count = 0
            while self.continue_iteration:
                iteration_count += 1
                self.log_progress(f"📊 ITERATION #{iteration_count} - Running analysis...")
                
                # Run analysis
                analysis = self.run_business_field_analysis()
                if analysis:
                    remaining_models = self.extract_remaining_models(analysis)
                    critical_count = self.extract_critical_fields_count(analysis)
                    
                    self.log_progress(f"📈 Status: {critical_count} critical fields, {len(remaining_models)} models remaining")
                    
                    if not remaining_models:
                        self.log_progress("🎉 ALL MODELS COMPLETED! No more critical missing fields!")
                        break
                        
                    # Display current status
                    self.log_progress(f"🎯 Next targets: {', '.join(remaining_models[:3])}")
                    
                else:
                    self.log_progress("❌ Analysis failed, stopping auto-iteration")
                    break
                    
                # Wait before next iteration
                time.sleep(2)
                
                # Safety check - stop after reasonable number of iterations
                if iteration_count > 50:
                    self.log_progress("🛑 Safety limit reached (50 iterations), stopping")
                    break
                    
        except KeyboardInterrupt:
            self.log_progress("🛑 Auto-iteration stopped by user")
        finally:
            self.continue_iteration = False
            self.log_session_summary()
            
    def log_session_summary(self):
        """Log final session summary"""
        duration = datetime.now() - self.session_stats['start_time']
        
        print("\n" + "="*60)
        print("📊 AUTO-ITERATION SESSION SUMMARY")
        print("="*60)
        print(f"⏱️  Duration: {duration}")
        print(f"🏢 Models Completed: {self.session_stats['models_completed']}")
        print(f"📝 Fields Implemented: {self.session_stats['fields_implemented']}")
        print(f"🐛 Errors Fixed: {self.session_stats['errors_fixed']}")
        print("="*60)

def main():
    """Main entry point"""
    print("🤖 AUTO-ITERATION MANAGER")
    print("This script will automatically continue iterations and track progress")
    print("Use this when you want to systematically work through all models")
    
    manager = AutoIterationManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--start':
        manager.start_auto_iteration()
    else:
        print("\n📋 Available commands:")
        print("  python3 auto_continue_iteration.py --start    # Start auto-iteration")
        print("  python3 auto_continue_iteration.py --status   # Check current status")
        
        # Show current status
        print("\n📊 CURRENT STATUS:")
        analysis = manager.run_business_field_analysis()
        if analysis:
            remaining_models = manager.extract_remaining_models(analysis)
            critical_count = manager.extract_critical_fields_count(analysis)
            print(f"🎯 Critical missing fields: {critical_count}")
            print(f"🏢 Models needing attention: {len(remaining_models)}")
            if remaining_models:
                print(f"📋 Next models to fix: {', '.join(remaining_models[:5])}")

if __name__ == "__main__":
    main()
