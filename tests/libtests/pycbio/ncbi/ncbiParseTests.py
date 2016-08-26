# Copyright 2006-2015 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.append("../../../../lib")

from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.ncbi.assembly import AssemblyReport


class NcbiParseTests(TestCaseBase):
    def testAssemblyReport(self):
        asmReport = AssemblyReport(self.getInputFile("GCF_000001405.28.assembly.txt"))
        seqLines = [str(seq) for seq in asmReport.seqs]
        self.assertEquals(seqLines,
                          ['1\tassembled-molecule\t1\tChromosome\tCM000663.2\t=\tNC_000001.11\tPrimary Assembly\t249698942\tchr1',
                           '2\tassembled-molecule\t2\tChromosome\tCM000664.2\t=\tNC_000002.12\tPrimary Assembly\t242508799\tchr2',
                           '3\tassembled-molecule\t3\tChromosome\tCM000665.2\t=\tNC_000003.12\tPrimary Assembly\t198450956\tchr3',
                           'Y\tassembled-molecule\tY\tChromosome\tCM000686.2\t=\tNC_000024.10\tPrimary Assembly\t57264655\tchrY',
                           'HSCHR1_CTG1_UNLOCALIZED\tunlocalized-scaffold\t1\tChromosome\tKI270706.1\t=\tNT_187361.1\tPrimary Assembly\t175055\tchr1_KI270706v1_random',
                           'HSCHRUN_RANDOM_CTG34\tunplaced-scaffold\tna\tna\tKI270755.1\t=\tNT_187510.1\tPrimary Assembly\t36723\tchrUn_KI270755v1',
                           'HG986_PATCH\tfix-patch\t1\tChromosome\tKN196472.1\t=\tNW_009646194.1\tPATCHES\t186494\tna',
                           'HSCHR5_7_CTG1\tnovel-patch\t5\tChromosome\tKN196477.1\t=\tNW_009646199.1\tPATCHES\t139087\tna',
                           'HG2128_PATCH\tfix-patch\t6\tChromosome\tKN196478.1\t=\tNW_009646200.1\tPATCHES\t268330\tna',
                           'HSCHR19KIR_T7526_BDEL_HAP_CTG3_1\talt-scaffold\t19\tChromosome\tKI270916.1\t=\tNT_187670.1\tALT_REF_LOCI_22\t184516\tchr19_KI270916v1_alt',
                           'MT\tassembled-molecule\tMT\tMitochondrion\tJ01415.2\t=\tNC_012920.1\tnon-nuclear\t16569\tchrM'])

        expectLine = 'HSCHR19KIR_T7526_BDEL_HAP_CTG3_1\talt-scaffold\t19\tChromosome\tKI270916.1\t=\tNT_187670.1\tALT_REF_LOCI_22\t184516\tchr19_KI270916v1_alt'
        self.assertEquals(str(asmReport.bySequenceName['HSCHR19KIR_T7526_BDEL_HAP_CTG3_1']), expectLine)
        self.assertEquals(str(asmReport.byGenBankAccn['KI270916.1']), expectLine)
        self.assertEquals(str(asmReport.byRefSeqAccn['NT_187670.1']), expectLine)
        self.assertEquals(str(asmReport.byUcscStyleName['chr19_KI270916v1_alt']), expectLine)

        metaData = [(name, asmReport.metaData[name]) for name in sorted(asmReport.metaData.iterkeys())]
        self.assertEquals(metaData,
                          [('Assembly Name', 'GRCh38.p2'),
                           ('Assembly level', 'Chromosome'),
                           ('Assembly type', 'haploid-with-alt-loci'),
                           ('Date', '2014-12-5'),
                           ('Description', 'Genome Reference Consortium Human Build 38 patch release 2 (GRCh38.p2)'),
                           ('GenBank Assembly Accession', 'GCA_000001405.17 (replaced)'),
                           ('Genome representation', 'full'),
                           ('Organism name', 'Homo sapiens'),
                           ('RefSeq Assembly Accession', 'GCF_000001405.28 (species-representative replaced)'),
                           ('RefSeq Assembly and GenBank Assemblies Identical', 'yes'),
                           ('Release type', 'patch'),
                           ('Submitter', 'Genome Reference Consortium'),
                           ('Taxid', '9606')])


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(NcbiParseTests))
    return ts

if __name__ == '__main__':
    unittest.main()
