"""Bundle canonical, non-private runtime resources when building a wheel."""

from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithResources(build_py):
    def run(self):
        super().run()
        root = Path(__file__).resolve().parent
        patterns = (
            "prompts/*.md",
            "dataset/labels.json",
            "dataset/rubrics/*.md",
            "dataset/rubrics/*.pdf",
            "dataset/submissions/*.txt",
            "dataset/submissions/*.pdf",
        )
        for pattern in patterns:
            for source in sorted(root.glob(pattern)):
                destination = Path(self.build_lib) / "rubric_agent" / "resources" / source.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                self.copy_file(str(source), str(destination))


setup(cmdclass={"build_py": BuildWithResources})
