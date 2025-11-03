"""
Service for handling LaTeX compilation.
"""
from dataclasses import dataclass
import os
import subprocess
import shutil
import glob
from typing import List, Optional


class LaTeXError(Exception):
    """Custom exception for LaTeX-related errors."""
    pass


@dataclass
class LaTeXConfig:
    """Configuration for LaTeX compilation."""
    keep_main_tex: bool = False
    keep_log_on_error: bool = True
    keep_log_on_success: bool = False
    num_passes: int = 3  # Number of compilation passes


class LaTeXService:
    """Service for handling LaTeX document compilation."""
    def __init__(self, config: LaTeXConfig = None):
        self.config = config or LaTeXConfig()

    def is_available(self) -> bool:
        """Check if pdflatex is available in the system."""
        return bool(shutil.which("pdflatex"))

    def _run_pdflatex(self, main_tex_path: str, output_dir: str, pass_num: int) -> subprocess.CompletedProcess:
        """Run a single pass of pdflatex."""
        print(f"  pdflatex Pass {pass_num}...")
        
        cmd = [
            "pdflatex",
            f"-output-directory={output_dir}",
            "-interaction=nonstopmode",
            "-file-line-error",
            main_tex_path
        ]

        try:
            return subprocess.run(
                cmd,
                cwd=output_dir,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"LaTeX compilation failed (Pass {pass_num}):\n"
            if e.stdout:
                error_msg += f"STDOUT:\n{e.stdout}\n"
            if e.stderr:
                error_msg += f"STDERR:\n{e.stderr}"
            raise LaTeXError(error_msg) from e
        except FileNotFoundError:
            raise LaTeXError("pdflatex command not found. Is it installed and in your PATH?")

    def compile_pdf(self, main_tex_path: str, output_dir: str) -> str:
        """
        Compile LaTeX to PDF.
        
        Args:
            main_tex_path: Path to main LaTeX file
            output_dir: Output directory for compilation
        
        Returns:
            Path to the generated PDF file
        
        Raises:
            LaTeXError: If compilation fails
            FileNotFoundError: If input file doesn't exist
        """
        if not os.path.exists(main_tex_path):
            raise FileNotFoundError(f"Input file not found: {main_tex_path}")

        print(f"\nCompiling '{os.path.basename(main_tex_path)}' to PDF...")

        # Run multiple passes for references and ToC
        for i in range(self.config.num_passes):
            self._run_pdflatex(main_tex_path, output_dir, i + 1)

        # Check for output PDF
        pdf_name = os.path.basename(main_tex_path).replace(".tex", ".pdf")
        pdf_path = os.path.join(output_dir, pdf_name)

        if not os.path.exists(pdf_path):
            log_file = os.path.join(output_dir, os.path.basename(main_tex_path).replace(".tex", ".log"))
            error_msg = f"\nError: PDF file '{pdf_path}' not found after compilation."
            if os.path.exists(log_file):
                error_msg += f"\nSee '{log_file}' for detailed LaTeX messages."
            raise LaTeXError(error_msg)

        print(f"\nSuccessfully compiled. PDF available at: '{pdf_path}'")
        return pdf_path

    def cleanup_files(self, output_dir: str, main_tex_filename: str) -> None:
        """
        Clean up intermediate LaTeX files.
        
        Args:
            output_dir: Directory containing the files to clean
            main_tex_filename: Name of the main TeX file
        """
        print("\nCleaning up intermediate files...")
        
        # Extensions to clean up
        extensions = ["aux", "toc", "out", "lof", "lot", "bbl", "blg", "synctex.gz"]
        if not self.config.keep_log_on_success:
            extensions.append("log")

        # Clean up each file type
        for ext in extensions:
            pattern = os.path.join(output_dir, f"*.{ext}")
            for f_path in glob.glob(pattern):
                # Skip log file if it should be kept
                if (ext == "log" and 
                    os.path.basename(f_path) == main_tex_filename.replace(".tex", ".log") and
                    self.config.keep_log_on_success):
                    continue
                try:
                    os.remove(f_path)
                    print(f"  Deleted '{os.path.basename(f_path)}'")
                except OSError as e:
                    print(f"  Error deleting '{os.path.basename(f_path)}': {e}")

        # Clean up temporary TeX files
        for f_path in glob.glob(os.path.join(output_dir, "tmp_*.tex")):
            try:
                os.remove(f_path)
                print(f"  Deleted '{os.path.basename(f_path)}'")
            except OSError as e:
                print(f"  Error deleting '{os.path.basename(f_path)}': {e}")

        # Handle main TeX file
        if not self.config.keep_main_tex:
            main_tex_path = os.path.join(output_dir, main_tex_filename)
            if os.path.exists(main_tex_path):
                try:
                    os.remove(main_tex_path)
                    print(f"  Deleted '{main_tex_filename}'")
                except OSError as e:
                    print(f"  Error deleting '{main_tex_filename}': {e}")
        else:
            print(f"  Kept '{main_tex_filename}' in '{output_dir}'.")

        # Report on log file status
        if self.config.keep_log_on_success:
            print(f"  Kept '{main_tex_filename.replace('.tex', '.log')}' in '{output_dir}'.")