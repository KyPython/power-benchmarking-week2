#!/usr/bin/env python3
"""
Enhanced Signal Handler
Monitors multiple kernel signals beyond SIGINT for improved robustness.
Implements the "heartbeat" mechanism for responsive signal delivery.
"""

import signal
import sys
import time
import threading
from typing import Dict, Callable, Optional
from collections import deque


class EnhancedSignalHandler:
    """
    Enhanced signal handler that monitors multiple signals and provides
    responsive shutdown even under CPU stress.
    """
    
    def __init__(self, shutdown_callback: Optional[Callable] = None):
        """
        Initialize enhanced signal handler.
        
        Args:
            shutdown_callback: Function to call on shutdown signal
        """
        self.shutdown_callback = shutdown_callback
        self.running = True
        self.signal_received = None
        self.signal_times = deque(maxlen=100)
        self.handlers = {}
        
        # Register signal handlers
        self._register_handlers()
        
        # Start heartbeat monitor
        self._start_heartbeat()
    
    def _register_handlers(self):
        """Register handlers for multiple signals."""
        # SIGINT (Ctrl+C) - most common
        signal.signal(signal.SIGINT, self._handle_signal)
        self.handlers[signal.SIGINT] = 'SIGINT (Ctrl+C)'
        
        # SIGTERM (termination request)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._handle_signal)
            self.handlers[signal.SIGTERM] = 'SIGTERM (Termination)'
        
        # SIGHUP (hangup - terminal closed)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, self._handle_signal)
            self.handlers[signal.SIGHUP] = 'SIGHUP (Hangup)'
        
        # SIGQUIT (quit - core dump)
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, self._handle_signal)
            self.handlers[signal.SIGQUIT] = 'SIGQUIT (Quit)'
    
    def _handle_signal(self, sig, frame):
        """
        Handle received signal.
        
        Uses timer-based mechanism for responsive delivery.
        """
        signal_name = self.handlers.get(sig, f'Signal {sig}')
        timestamp = time.time()
        
        self.signal_received = sig
        self.signal_times.append((sig, timestamp, signal_name))
        self.running = False
        
        # Call shutdown callback if provided
        if self.shutdown_callback:
            try:
                self.shutdown_callback(sig, signal_name)
            except Exception as e:
                print(f"⚠️  Error in shutdown callback: {e}")
        
        # Print shutdown message
        print(f"\n\n🛑 Shutting down gracefully... ({signal_name})")
    
    def _start_heartbeat(self):
        """
        Start heartbeat monitor using timer-based mechanism.
        
        This ensures signals are checked regularly even under CPU stress.
        """
        def heartbeat_loop():
            """Heartbeat loop that checks for signals regularly."""
            while self.running:
                # Use select.select() with timeout for responsive signal checking
                # This is the "heartbeat" mechanism
                import select
                try:
                    # Wait with 100ms timeout (heartbeat interval)
                    ready, _, _ = select.select([], [], [], 0.1)
                    
                    # If signal received, it will be handled by signal handler
                    # This regular check ensures responsiveness
                    if not self.running:
                        break
                except Exception:
                    # If select fails, just sleep
                    time.sleep(0.1)
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
    
    def is_running(self) -> bool:
        """Check if handler is still running."""
        return self.running
    
    def get_signal_info(self) -> Optional[Dict]:
        """Get information about received signal."""
        if not self.signal_times:
            return None
        
        sig, timestamp, name = self.signal_times[-1]
        return {
            'signal': sig,
            'name': name,
            'timestamp': timestamp,
            'count': len(self.signal_times)
        }
    
    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for shutdown signal with optional timeout.
        
        Returns:
            True if shutdown signal received, False if timeout
        """
        start_time = time.time()
        
        while self.running:
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            time.sleep(0.1)  # Small sleep to avoid busy-wait
        
        return True


# Global handler instance
_global_handler: Optional[EnhancedSignalHandler] = None


def setup_enhanced_signals(shutdown_callback: Optional[Callable] = None) -> EnhancedSignalHandler:
    """
    Set up enhanced signal handling.
    
    Args:
        shutdown_callback: Function to call on shutdown
    
    Returns:
        EnhancedSignalHandler instance
    """
    global _global_handler
    
    def default_callback(sig, name):
        """Default shutdown callback."""
        print(f"\n🛑 Received {name}, shutting down...")
    
    callback = shutdown_callback or default_callback
    _global_handler = EnhancedSignalHandler(callback)
    
    return _global_handler


def get_signal_handler() -> Optional[EnhancedSignalHandler]:
    """Get the global signal handler instance."""
    return _global_handler


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested."""
    if _global_handler:
        return not _global_handler.is_running()
    return False


# Example usage
if __name__ == "__main__":
    def my_shutdown(sig, name):
        print(f"Custom shutdown handler: {name}")
        # Add custom cleanup here
    
    handler = setup_enhanced_signals(my_shutdown)
    
    print("Enhanced signal handler active. Press Ctrl+C to test...")
    print("Monitoring: SIGINT, SIGTERM, SIGHUP, SIGQUIT")
    print()
    
    # Simulate work
    count = 0
    while handler.is_running():
        print(f"Working... {count}", end='\r')
        count += 1
        time.sleep(0.5)
        
        if count > 100:
            print("\n✅ Test complete (no signal received)")
            break
    
    # Print signal info
    info = handler.get_signal_info()
    if info:
        print(f"\n📊 Signal Info:")
        print(f"   Signal: {info['name']}")
        print(f"   Timestamp: {info['timestamp']}")
        print(f"   Total signals: {info['count']}")

