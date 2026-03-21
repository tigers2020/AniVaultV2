"""signals.py

GUI 이벤트 시그널 모음(탭 전환, 시뮬레이션 등). 위젯별 시그널은 각 클래스에 정의.

Author: Pom Kim
"""

# Signals are defined on widgets (Sidebar.tab_clicked, Topbar.simulate_clicked).
# This module can hold shared signal objects if we need app-level bus later.
# For now, wiring is done in app.py (MainWindow).
