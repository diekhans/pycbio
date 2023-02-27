# Copyright 2006-2022 Mark Diekhans
import unittest
import sys
if __name__ == '__main__':
    sys.path.insert(0, "../../../../lib")

from pycbio import PycbioException
from pycbio.sys.testCaseBase import TestCaseBase
from pycbio.ncbi.assembly import AssemblyReport
from pycbio.ncbi.agp import Agp


class NcbiParseTests(TestCaseBase):
    def testAssemblyReport(self):
        asmReport = AssemblyReport(self.getInputFile("GCF_000001405.28.assembly.txt"))
        seqLines = [str(seq) for seq in asmReport.seqs]
        self.assertEqual(seqLines,
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
        self.assertEqual(str(asmReport.getBySequenceName('HSCHR19KIR_T7526_BDEL_HAP_CTG3_1')), expectLine)
        self.assertEqual(str(asmReport.getByGenBankAccn('KI270916.1')), expectLine)
        self.assertEqual(str(asmReport.getByRefSeqAccn('NT_187670.1')), expectLine)
        self.assertEqual(str(asmReport.getByUcscStyleName('chr19_KI270916v1_alt')), expectLine)

        for name in ('HSCHR19KIR_T7526_BDEL_HAP_CTG3_1', 'KI270916.1', 'NT_187670.1', 'chr19_KI270916v1_alt'):
            self.assertEqual(str(asmReport.getByName(name)), expectLine)

        metaData = sorted(list(asmReport.metaData.items()))
        self.assertEqual(metaData,
                         [('assembly_level', 'Chromosome'),
                          ('assembly_name', 'GRCh38.p2'),
                          ('assembly_type', 'haploid-with-alt-loci'),
                          ('date', '2014-12-5'),
                          ('description', 'Genome Reference Consortium Human Build 38 patch release 2 (GRCh38.p2)'),
                          ('genbank_assembly_accession', 'GCA_000001405.17 (replaced)'),
                          ('genome_representation', 'full'),
                          ('organism_name', 'Homo sapiens'),
                          ('refseq_assembly_accession', 'GCF_000001405.28 (species-representative replaced)'),
                          ('refseq_assembly_and_genbank_assemblies_identical', 'yes'),
                          ('release_type', 'patch'),
                          ('submitter', 'Genome Reference Consortium'),
                          ('taxid', '9606')])
        self.assertEqual(asmReport.assemblyName, 'GRCh38.p2')
        with self.assertRaisesRegex(PycbioException, "^sequence 'fred' not found in NCBI AssemblyReport for 'GRCh38.p2'$"):
            asmReport.getByName("fred")

    def testAssemblyReportNewMeta(self):
        # updated metadata name capitalization
        asmReport = AssemblyReport(self.getInputFile("GCF_000001405.39_GRCh38.p13_assembly_report.txt"))
        self.assertEqual(asmReport.assemblyName, 'GRCh38.p13')
        metaData = sorted(list(asmReport.metaData.items()))
        self.assertEqual(metaData,
                         [('assembly_level', 'Chromosome'),
                          ('assembly_name', 'GRCh38.p13'),
                          ('assembly_type', 'haploid-with-alt-loci'),
                          ('bioproject', 'PRJNA31257'),
                          ('date', '2019-02-28'),
                          ('description', 'Genome Reference Consortium Human Build 38 patch release 13 (GRCh38.p13)'),
                          ('genbank_assembly_accession', 'GCA_000001405.28'),
                          ('genome_representation', 'full'),
                          ('organism_name', 'Homo sapiens (human)'),
                          ('refseq_assembly_accession', 'GCF_000001405.39'),
                          ('refseq_assembly_and_genbank_assemblies_identical', 'no'),
                          ('refseq_category', 'Reference Genome'),
                          ('release_type', 'patch'),
                          ('submitter', 'Genome Reference Consortium'),
                          ('synonyms', 'hg38'),
                          ('taxid', '9606')])
        with self.assertRaisesRegex(PycbioException, "^sequence 'fred' not found in NCBI AssemblyReport for 'GRCh38.p13'$"):
            asmReport.getByName("fred")

    def testAgpGrch38(self):
        agp = Agp(self.getInputFile("GCA_000001305.2.chr22.agp"))
        agpRows = [rec.format(True) for rec in agp.recs]
        self.assertEqual(agpRows,
                         ['CM000684.2\t1\t10000\t1\tN\t10000\ttelomere\tno\tna',
                          'CM000684.2\t10001\t10510000\t2\tN\t10500000\tshort_arm\tno\tna',
                          'CM000684.2\t10510001\t10784643\t3\tF\tGL000217.2\t1\t274643\t+',
                          'CM000684.2\t10784644\t10834643\t4\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t10834644\t10874572\t5\tF\tGL000244.1\t1\t39929\t+',
                          'CM000684.2\t10874573\t10924572\t6\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t10924573\t10966724\t7\tF\tGL000241.1\t1\t42152\t+',
                          'CM000684.2\t10966725\t11016724\t8\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11016725\t11068987\t9\tF\tGL000237.2\t1\t52263\t+',
                          'CM000684.2\t11068988\t11118987\t10\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11118988\t11160921\t11\tF\tGL000236.1\t1\t41934\t+',
                          'CM000684.2\t11160922\t11210921\t12\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11210922\t11378056\t13\tF\tKI270657.1\t1\t167135\t+',
                          'CM000684.2\t11378057\t11428056\t14\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11428057\t11497337\t15\tF\tGL000233.2\t1\t69281\t+',
                          'CM000684.2\t11497338\t11547337\t16\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11547338\t11631288\t17\tF\tKI270658.1\t1\t83951\t+',
                          'CM000684.2\t11631289\t11681288\t18\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11681289\t11724629\t19\tF\tGL000243.1\t1\t43341\t+',
                          'CM000684.2\t11724630\t11774629\t20\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t11774630\t11977555\t21\tF\tKI270659.1\t1\t202926\t+',
                          'CM000684.2\t11977556\t12027555\t22\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12027556\t12225588\t23\tF\tKI270660.1\t1\t198033\t+',
                          'CM000684.2\t12225589\t12275588\t24\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12275589\t12438690\t25\tF\tKI270661.1\t1\t163102\t+',
                          'CM000684.2\t12438691\t12488690\t26\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12488691\t12641730\t27\tF\tKI270662.1\t1\t153040\t+',
                          'CM000684.2\t12641731\t12691730\t28\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12691731\t12726204\t29\tF\tGL000235.1\t1\t34474\t+',
                          'CM000684.2\t12726205\t12776204\t30\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12776205\t12818137\t31\tF\tGL000240.1\t1\t41933\t+',
                          'CM000684.2\t12818138\t12868137\t32\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12868138\t12904788\t33\tF\tGL000245.1\t1\t36651\t+',
                          'CM000684.2\t12904789\t12954788\t34\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t12954789\t12977325\t35\tF\tKI270663.1\t1\t22537\t+',
                          'CM000684.2\t12977326\t12977425\t36\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t12977426\t13021322\t37\tF\tKI270436.1\t1\t43897\t+',
                          'CM000684.2\t13021323\t13021422\t38\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13021423\t13109444\t39\tF\tKI270669.1\t1\t88022\t+',
                          'CM000684.2\t13109445\t13109544\t40\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13109545\t13163677\t41\tF\tKI270670.1\t1\t54133\t+',
                          'CM000684.2\t13163678\t13163777\t42\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13163778\t13227312\t43\tF\tKI270671.1\t1\t63535\t+',
                          'CM000684.2\t13227313\t13227412\t44\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13227413\t13248082\t45\tF\tKI270673.1\t1\t20670\t+',
                          'CM000684.2\t13248083\t13248182\t46\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13248183\t13254852\t47\tF\tKI270675.1\t1\t6670\t+',
                          'CM000684.2\t13254853\t13254952\t48\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13254953\t13258197\t49\tF\tKI270676.1\t1\t3245\t+',
                          'CM000684.2\t13258198\t13258297\t50\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13258298\t13280858\t51\tF\tKI270677.1\t1\t22561\t+',
                          'CM000684.2\t13280859\t13280958\t52\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13280959\t13285143\t53\tF\tKI270449.1\t1\t4185\t+',
                          'CM000684.2\t13285144\t13285243\t54\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t13285244\t14419454\t55\tF\tKI270680.1\t1\t1134211\t+',
                          'CM000684.2\t14419455\t14419554\t56\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t14419555\t14419894\t57\tF\tKI866541.1\t1\t340\t+',
                          'CM000684.2\t14419895\t14419994\t58\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t14419995\t14420334\t59\tF\tKI866542.1\t1\t340\t+',
                          'CM000684.2\t14420335\t14420434\t60\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t14420435\t14421632\t61\tF\tKI270694.1\t1\t1198\t+',
                          'CM000684.2\t14421633\t14421732\t62\tN\t100\tcontig\tno\tna',
                          'CM000684.2\t14421733\t15054318\t63\tF\tKI270699.1\t1\t632586\t+',
                          'CM000684.2\t15054319\t15154318\t64\tN\t100000\tcontig\tno\tna',
                          'CM000684.2\t15154319\t18239129\t65\tF\tKI270700.1\t1\t3084811\t+',
                          'CM000684.2\t18239130\t18339129\t66\tN\t100000\tcontig\tno\tna',
                          'CM000684.2\t18339130\t18433513\t67\tF\tKI270701.1\t1\t94384\t+',
                          'CM000684.2\t18433514\t18483513\t68\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t18483514\t18659564\t69\tF\tKI270702.1\t1\t176051\t+',
                          'CM000684.2\t18659565\t18709564\t70\tN\t50000\tcontig\tno\tna',
                          'CM000684.2\t18709565\t49973865\t71\tF\tGL000155.2\t1\t31264301\t+',
                          'CM000684.2\t49973866\t49975365\t72\tN\t1500\tcontig\tno\tna',
                          'CM000684.2\t49975366\t50808468\t73\tF\tGL000156.2\t1\t833103\t+',
                          'CM000684.2\t50808469\t50818468\t74\tN\t10000\ttelomere\tno\tna'])

    def testAgpClint(self):
        agp = Agp(self.getInputFile("GCA_002880755.3.chr10.agp"))
        agpRows = [rec.format(True) for rec in agp.recs]
        self.assertEqual(agpRows,
                         ['CM009248.2\t1\t19390040\t1\tW\tKZ622779.1\t1\t19390040\t-',
                          'CM009248.2\t19390041\t19390140\t2\tU\t100\tcontig\tno\tna',
                          'CM009248.2\t19390141\t38555298\t3\tW\tKZ622780.1\t1\t19165158\t+',
                          'CM009248.2\t38555299\t38555398\t4\tU\t100\tcontig\tno\tna',
                          'CM009248.2\t38555399\t75251514\t5\tW\tKZ622781.1\t1\t36696116\t-',
                          'CM009248.2\t75251515\t75251614\t6\tU\t100\tcontig\tno\tna',
                          'CM009248.2\t75251615\t127816455\t7\tW\tKZ622782.1\t1\t52564841\t+',
                          'CM009248.2\t127816456\t127816555\t8\tU\t100\tcontig\tno\tna',
                          'CM009248.2\t127816556\t129809613\t9\tW\tKZ622783.1\t1\t1993058\t+'])


def suite():
    ts = unittest.TestSuite()
    ts.addTest(unittest.makeSuite(NcbiParseTests))
    return ts


if __name__ == '__main__':
    unittest.main()
