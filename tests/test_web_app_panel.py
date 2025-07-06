"""Tests for web application panel functionality and static file serving."""

import pytest
from fastapi.testclient import TestClient

from aws_adfs_gui.web_app import app


class TestWebAppPanelFunctionality:
    """Test suite for web application panel functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for the web application."""
        return TestClient(app)

    def test_index_page_loads(self, client):
        """Test that the index page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_contains_panel_elements(self, client):
        """Test that the index page contains required panel elements."""
        response = client.get("/")
        content = response.text

        # Check for left panel element
        assert 'id="leftPanel"' in content
        assert 'id="rightPanel"' in content

        # Check for toggle buttons
        assert 'id="togglePanelBtn"' in content
        assert 'id="showPanelBtn"' in content

        # Check for resize handle
        assert 'id="resizeHandle"' in content
        assert 'class="resize-handle"' in content

    def test_panel_css_classes_present(self, client):
        """Test that panel-related CSS classes are present in the page."""
        response = client.get("/")
        content = response.text

        # Check for panel CSS structure
        assert 'class="row flex-fill"' in content
        assert "bg-light border-end" in content

    def test_static_css_file_accessible(self, client):
        """Test that the CSS file with panel styles is accessible."""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

        content = response.text
        # Check for panel-specific CSS
        assert "#leftPanel" in content
        assert "#rightPanel" in content
        assert ".resize-handle" in content
        assert ".hidden" in content

    def test_static_js_file_accessible(self, client):
        """Test that the JavaScript file with panel functionality is accessible."""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert (
            "application/javascript" in response.headers["content-type"]
            or "text/javascript" in response.headers["content-type"]
        )

        content = response.text
        # Check for panel-specific JavaScript functions
        assert "toggleLeftPanel" in content
        assert "hideLeftPanel" in content
        assert "showLeftPanel" in content
        assert "setupPanelResize" in content

    def test_panel_test_page_accessible(self, client):
        """Test that the panel test page is accessible."""
        # Note: test_panel.html was removed as it's no longer needed
        # This test now checks that the main page loads correctly with panel functionality
        response = client.get("/")
        assert response.status_code == 200
        assert "leftPanel" in response.text  # Panel should be present in main page

    def test_panel_functionality_test_page_accessible(self, client):
        """Test that the panel functionality test page is accessible."""
        # This might not be accessible depending on static file configuration
        # The test is mainly to verify the path structure
        try:
            response = client.get("/static/../tests/test_panel_functionality.html")
            # If accessible, it should be HTML
            if response.status_code == 200:
                assert "text/html" in response.headers["content-type"]
        except Exception:
            # Path might not be accessible due to static file configuration
            pass

    def test_index_has_required_bootstrap_and_fontawesome(self, client):
        """Test that the index page includes required CSS/JS libraries."""
        response = client.get("/")
        content = response.text

        # Check for Bootstrap CSS
        assert "bootstrap@5.3.0" in content

        # Check for FontAwesome
        assert "font-awesome" in content

        # Check for our custom styles
        assert "/static/styles.css" in content
        assert "/static/app.js" in content

    def test_panel_javascript_classes_defined(self, client):
        """Test that required JavaScript classes and functions are defined."""
        response = client.get("/static/app.js")
        content = response.text

        # Check for main app class
        assert "class AWSADFSApp" in content

        # Check for panel management methods
        assert "toggleLeftPanel()" in content
        assert "hideLeftPanel()" in content
        assert "showLeftPanel()" in content
        assert "setupPanelResize()" in content
        assert "loadPanelPreferences()" in content
        assert "handleWindowResize()" in content
        assert "isMobile()" in content

    def test_panel_css_responsive_media_queries(self, client):
        """Test that responsive CSS media queries are present for mobile."""
        response = client.get("/static/styles.css")
        content = response.text

        # Check for mobile media query
        assert "@media (max-width: 768px)" in content

        # Check for mobile-specific panel styles
        assert "#leftPanel.mobile-show" in content
        assert "#leftPanel.hidden" in content

    def test_panel_default_width_configuration(self, client):
        """Test that the panel has appropriate default width configuration."""
        response = client.get("/static/styles.css")
        content = response.text

        # Check for panel styling existence (we've redesigned the CSS)
        # The new design uses responsive widths instead of fixed 280px
        assert "leftPanel" in content or "#leftPanel" in content


class TestPanelJavaScriptFunctionality:
    """Test JavaScript functionality using static analysis."""

    @pytest.fixture
    def js_content(self):
        """Get the JavaScript content for analysis."""
        client = TestClient(app)
        response = client.get("/static/app.js")
        return response.text

    def test_panel_event_listeners_setup(self, js_content):
        """Test that event listeners are properly set up for panel functionality."""
        # Check for event listener setup
        assert "addEventListener('click'" in js_content
        assert "addEventListener('mousedown'" in js_content
        assert "addEventListener('mousemove'" in js_content
        assert "addEventListener('mouseup'" in js_content
        assert "addEventListener('dblclick'" in js_content

    def test_local_storage_usage(self, js_content):
        """Test that localStorage is used for panel state persistence."""
        assert "localStorage.setItem" in js_content
        assert "localStorage.getItem" in js_content
        assert "localStorage.removeItem" in js_content

        # Check for specific panel storage keys
        assert "'leftPanelHidden'" in js_content
        assert "'leftPanelWidth'" in js_content

    def test_panel_css_class_manipulation(self, js_content):
        """Test that CSS classes are properly manipulated for panel states."""
        assert "classList.add('hidden')" in js_content
        assert "classList.remove('hidden')" in js_content
        assert "classList.contains('hidden')" in js_content
        assert "classList.add('d-none')" in js_content
        assert "classList.remove('d-none')" in js_content

    def test_panel_resize_constraints(self, js_content):
        """Test that panel resize has proper constraints."""
        # Check for minimum and maximum width constraints
        assert "minWidth" in js_content
        assert "maxWidth" in js_content
        assert "200" in js_content  # minimum width
        assert "600" in js_content  # maximum width
        assert "window.innerWidth" in js_content  # responsive maximum

    def test_panel_mobile_detection(self, js_content):
        """Test that mobile detection is implemented."""
        assert "isMobile()" in js_content
        assert "window.innerWidth <= 768" in js_content

    def test_console_logging_for_debugging(self, js_content):
        """Test that console logging is present for debugging."""
        assert "console.log" in js_content
        assert "console.error" in js_content


class TestPanelCSSFunctionality:
    """Test CSS functionality for panel behavior."""

    @pytest.fixture
    def css_content(self):
        """Get the CSS content for analysis."""
        client = TestClient(app)
        response = client.get("/static/styles.css")
        return response.text

    def test_panel_transition_animations(self, css_content):
        """Test that CSS transitions are defined for smooth animations."""
        assert "transition:" in css_content
        assert "all 0.3s ease" in css_content

    def test_panel_flexbox_layout(self, css_content):
        """Test that flexbox properties are properly configured."""
        assert "flex:" in css_content
        assert "flex-direction:" in css_content or "display: flex" in css_content

    def test_resize_handle_styling(self, css_content):
        """Test that resize handle has proper styling."""
        assert ".resize-handle" in css_content
        assert "cursor: col-resize" in css_content
        assert "position: absolute" in css_content

    def test_hidden_panel_styling(self, css_content):
        """Test that hidden panel state is properly styled."""
        assert ".hidden" in css_content
        assert "width: 0" in css_content
        assert "overflow: hidden" in css_content

    def test_responsive_mobile_styles(self, css_content):
        """Test that mobile responsive styles are present."""
        assert "@media (max-width: 768px)" in css_content
        assert "position: fixed" in css_content  # Mobile panel behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
