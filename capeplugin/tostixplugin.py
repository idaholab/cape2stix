# Copyright 2023, Battelle Energy Alliance, LLC
from lib.cuckoo.common.abstracts import Report
from lib.cuckoo.common.constants import CUCKOO_ROOT
from lib.cuckoo.common.exceptions import CuckooReportError
from cape2stix.convert import Cape2STIX

class STIXPlugin(Report):
    """Gens STIX bundle as output """

    def run(self, results: dict):
        """Runs STIX processing
        @return: Nothing.  Results of this processing are obtained at an arbitrary future time.
        """
        try:
            basedir = os.path.join(CUCKOO_ROOT, "storage", "stix")
            reportsdir = os.path.join(basedir, "reports")
            task_id = str(results["info"]["id"])
            outputfile = os.path.join(basedir, f"{task_id}_STIX.json")
            with contextlib.suppress(Exception):
                os.makedirs(reportsdir)
            cs = Cape2STIX(data = results)
            cs.convert(outpath=outputfile)

        except Exception as e:
            raise CuckooReportError(f"Failed to perform STIX conversion: {e}") from e