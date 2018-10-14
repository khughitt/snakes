"""
SnakefileRenderer test code
"""
import os

class TestRenderer():
    def test_snakefile_render(self, renderer):
        # Render Snakefile and check for output file
        renderer.render()
        assert os.path.exists(nb1.output_file)

