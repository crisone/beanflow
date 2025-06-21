#!/usr/bin/env python3
"""
Beanflow CLI tool for importing financial data
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from beanflow.importer.alipay import AlipayImporter
from beanflow.importer.wechat import WechatImporter
from beanflow.importer.jd import JdImporter  # Temporarily disabled due to import issues
from beanflow.importer.meituan import MeituanImporter

# Placeholder classes for unimplemented importers
class CCBImporter:
    def __init__(self):
        raise NotImplementedError("CCB importer is not yet implemented")

class HSBCImporter:
    def __init__(self):
        raise NotImplementedError("HSBC importer is not yet implemented")


class BeanflowCLI:
    """Main CLI class for Beanflow"""
    
    def __init__(self):
        self.importers = {
            'alipay': AlipayImporter,
            'wechat': WechatImporter,
            'jd': JdImporter,  # Temporarily disabled
            'meituan': MeituanImporter,
            # 'ccb': CCBImporter,  # Not implemented yet
            # 'hsbc': HSBCImporter,  # Not implemented yet
        }
    
    def create_parser(self):
        """Create the argument parser"""
        parser = argparse.ArgumentParser(
            description='Beanflow - A tool for importing financial data into Beancount',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  beanflow import -e alipay extract /path/to/alipay.csv
  beanflow import -e wechat extract /path/to/wechat.csv
  beanflow import -e meituan extract /path/to/meituan.csv
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Import command
        import_parser = subparsers.add_parser('import', help='Import financial data')
        import_parser.add_argument(
            '-e', '--exporter',
            required=True,
            choices=list(self.importers.keys()),
            help='Type of exporter to use'
        )
        # Don't add file argument here - let beangulp.testing.main handle it
        import_parser.add_argument(
            'args',
            nargs=argparse.REMAINDER,
            help='Arguments to pass to the importer (command and file path)'
        )
        
        return parser
    
    def run_import(self, args):
        """Run the import command by calling beangulp.testing.main"""
        if args.exporter not in self.importers:
            print(f"Error: Unknown exporter '{args.exporter}'", file=sys.stderr)
            return 1
        
        importer_class = self.importers[args.exporter]
        try:
            importer = importer_class()
        except NotImplementedError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        
        # Import beangulp.testing.main
        from beangulp.testing import main
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Construct new sys.argv for beangulp.testing.main
            # It expects: [script_name, command, file_path, ...]
            new_argv = [sys.argv[0]] + args.args
            sys.argv = new_argv
            
            # Call main with just the importer - it will read from sys.argv automatically
            return main(importer)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
    
    def run(self, args=None):
        """Main entry point"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        if parsed_args.command == 'import':
            return self.run_import(parsed_args)
        
        return 0


def main():
    """CLI entry point"""
    cli = BeanflowCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main() 