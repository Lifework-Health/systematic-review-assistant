from __future__ import annotations

import typing as t


def extract_text(element: t.Any) -> str:
    """Extract text from an element that might be a dict with a '_value' key.

    Extract text from a dict with '_value' key, a custom object with '_value'
    attribute, or already a plain string.
    """
    if isinstance(element, dict):
        return element.get("_value", str(element))
    if hasattr(element, "_value"):
        return element._value  # noqa: SLF001
    return str(element)


def recursive_clean(data: t.Any) -> list[t.Any] | dict[str, t.Any] | str:
    """Recursively convert custom objects into plain Python types.

    Converts custom objects (like StringElement or DictElement) into plain Python
    types like lists, dicts, and strings.
    """
    if isinstance(data, list):
        return [recursive_clean(item) for item in data]
    if isinstance(data, dict):
        return {k: recursive_clean(v) for k, v in data.items()}
    # If the object has 'attributes' (e.g., custom element), try to extract _value
    if hasattr(data, "attributes"):
        # If it also has _value, use that
        if hasattr(data, "_value"):
            return data._value  # noqa: SLF001
        # Otherwise, convert the whole thing to string
        return str(data)
    return data


# An example records:
# In [62]: records
# Out[62]:
# {'PubmedBookArticle': [], 'PubmedArticle': [{'MedlineCitation': DictElement({'GeneralNote': [], 'OtherAbstract': [], 'OtherID': [], 'CitationSubset': ['IM'], 'KeywordList': [ListElement([StringElement('AI regulation', attributes={'MajorTopicYN': 'N'}), StringElement('artificial intelligence', attributes={'MajorTopicYN': 'N'}), StringElement('healthcare competencies', attributes={'MajorTopicYN': 'N'}), StringElement('healthcare education', attributes={'MajorTopicYN': 'N'}), StringElement('systematic review', attributes={'MajorTopicYN': 'N'})], attributes={'Owner': 'NOTNLM'})], 'InvestigatorList': [], 'SpaceFlightMission': [], 'PMID': StringElement('39912237', attributes={'Version': '1'}), 'DateCompleted': {'Year': '2025', 'Month': '02', 'Day': '06'}, 'DateRevised': {'Year': '2025', 'Month': '02', 'Day': '15'}, 'Article': DictElement({'Language': ['eng'], 'ArticleDate': [DictElement({'Year': '2025', 'Month': '02', 'Day': '05'}, attributes={'DateType': 'Electronic'})], 'ELocationID': [StringElement('e58161', attributes={'EIdType': 'pii', 'ValidYN': 'Y'}), StringElement('10.2196/58161', attributes={'EIdType': 'doi', 'ValidYN': 'Y'})], 'Journal': {'ISSN': StringElement('2369-3762', attributes={'IssnType': 'Electronic'}), 'JournalIssue': DictElement({'Volume': '11', 'PubDate': {'Year': '2025', 'Month': 'Feb', 'Day': '05'}}, attributes={'CitedMedium': 'Internet'}), 'Title': 'JMIR medical education', 'ISOAbbreviation': 'JMIR Med Educ'}, 'ArticleTitle': 'AI in the Health Sector: Systematic Review of Key Skills for Future Health Professionals.', 'Pagination': {'StartPage': 'e58161', 'MedlinePgn': 'e58161'}, 'Abstract': {'AbstractText': [StringElement('Technological advancements have significantly reshaped health care, introducing digital solutions that enhance diagnostics and patient care. Artificial intelligence (AI) stands out, offering unprecedented capabilities in data analysis, diagnostic support, and personalized medicine. However, effectively integrating AI into health care necessitates specialized competencies among professionals, an area still in its infancy in terms of comprehensive literature and formalized training programs.', attributes={'Label': 'BACKGROUND', 'NlmCategory': 'UNASSIGNED'}), StringElement('This systematic review aims to consolidate the essential skills and knowledge health care professionals need to integrate AI into their clinical practice effectively, according to the published literature.', attributes={'Label': 'OBJECTIVE', 'NlmCategory': 'UNASSIGNED'}), StringElement("We conducted a systematic review, across databases PubMed, Scopus, and Web of Science, of peer-reviewed literature that directly explored the required skills for health care professionals to integrate AI into their practice, published in English or Spanish from 2018 onward. Studies that did not refer to specific skills or training in digital health were not included, discarding those that did not directly contribute to understanding the competencies necessary to integrate AI into health care practice. Bias in the examined works was evaluated following Cochrane's domain-based recommendations.", attributes={'Label': 'METHODS', 'NlmCategory': 'UNASSIGNED'}), StringElement('The initial database search yielded a total of 2457 articles. After deleting duplicates and screening titles and abstracts, 37 articles were selected for full-text review. Out of these, only 7 met all the inclusion criteria for this systematic review. The review identified a diverse range of skills and competencies, that we categorized into 14 key areas classified based on their frequency of appearance in the selected studies, including AI fundamentals, data analytics and management, and ethical considerations.', attributes={'Label': 'RESULTS', 'NlmCategory': 'UNASSIGNED'}), StringElement('Despite the broadening of search criteria to capture the evolving nature of AI in health care, the review underscores a significant gap in focused studies on the required competencies. Moreover, the review highlights the critical role of regulatory bodies such as the US Food and Drug Administration in facilitating the adoption of AI technologies by establishing trust and standardizing algorithms. Key areas were identified for developing competencies among health care professionals for the implementation of AI, including: AI fundamentals knowledge (more focused on assessing the accuracy, reliability, and validity of AI algorithms than on more technical abilities such as programming or mathematics), data analysis skills (including data acquisition, cleaning, visualization, management, and governance), and ethical and legal considerations. In an AI-enhanced health care landscape, the ability to humanize patient care through effective communication is paramount. This balance ensures that while AI streamlines tasks and potentially increases patient interaction time, health care professionals maintain a focus on compassionate care, thereby leveraging AI to enhance, rather than detract from, the patient experience.\u2003.', attributes={'Label': 'CONCLUSIONS', 'NlmCategory': 'UNASSIGNED'})], 'CopyrightInformation': '© Javier Gazquez-Garcia, Carlos Luis Sánchez-Bocanegra, Jose Luis Sevillano. Originally published in JMIR Medical Education (https://mededu.jmir.org).'}, 'AuthorList': ListElement([DictElement({'Identifier': [StringElement('0009-0005-0437-0708', attributes={'Source': 'ORCID'})], 'AffiliationInfo': [{'Identifier': [], 'Affiliation': 'Servicio Andaluz de Salud, Distrito Sanitario Almeria, Almeria, Spain.'}], 'LastName': 'Gazquez-Garcia', 'ForeName': 'Javier', 'Initials': 'J'}, attributes={'ValidYN': 'Y'}), DictElement({'Identifier': [StringElement('0000-0001-7033-5971', attributes={'Source': 'ORCID'})], 'AffiliationInfo': [{'Identifier': [], 'Affiliation': 'Faculty of Health Sciences, Universidad Oberta de Catalunya (UOC), Barcelona, Spain.'}], 'LastName': 'Sánchez-Bocanegra', 'ForeName': 'Carlos Luis', 'Initials': 'CL'}, attributes={'ValidYN': 'Y'}), DictElement({'Identifier': [StringElement('0000-0002-1392-1832', attributes={'Source': 'ORCID'})], 'AffiliationInfo': [{'Identifier': [], 'Affiliation': 'Universidad de Sevilla, ETS Ingenieria Informatica, Avda Reina Mercedes s/n, Sevilla, 41012, Spain, 34954556142.'}], 'LastName': 'Sevillano', 'ForeName': 'Jose Luis', 'Initials': 'JL'}, attributes={'ValidYN': 'Y'})], attributes={'CompleteYN': 'Y'}), 'PublicationTypeList': [StringElement('Journal Article', attributes={'UI': 'D016428'}), StringElement('Systematic Review', attributes={'UI': 'D000078182'}), StringElement('Review', attributes={'UI': 'D016454'})]}, attributes={'PubModel': 'Electronic'}), 'MedlineJournalInfo': {'Country': 'Canada', 'MedlineTA': 'JMIR Med Educ', 'NlmUniqueID': '101684518', 'ISSNLinking': '2369-3762'}, 'MeshHeadingList': [{'QualifierName': [], 'DescriptorName': StringElement('Artificial Intelligence', attributes={'UI': 'D001185', 'MajorTopicYN': 'Y'})}, {'QualifierName': [], 'DescriptorName': StringElement('Humans', attributes={'UI': 'D006801', 'MajorTopicYN': 'N'})}, {'QualifierName': [StringElement('education', attributes={'UI': 'Q000193', 'MajorTopicYN': 'N'})], 'DescriptorName': StringElement('Health Personnel', attributes={'UI': 'D006282', 'MajorTopicYN': 'Y'})}, {'QualifierName': [], 'DescriptorName': StringElement('Health Care Sector', attributes={'UI': 'D019981', 'MajorTopicYN': 'N'})}, {'QualifierName': [], 'DescriptorName': StringElement('Clinical Competence', attributes={'UI': 'D002983', 'MajorTopicYN': 'N'})}, {'QualifierName': [], 'DescriptorName': StringElement('Delivery of Health Care', attributes={'UI': 'D003695', 'MajorTopicYN': 'N'})}], 'CoiStatement': 'None declared.'}, attributes={'Status': 'MEDLINE', 'Owner': 'NLM', 'IndexingMethod': 'Automated'}), 'PubmedData': {'ReferenceList': [{'ReferenceList': [], 'Reference': [{'Citation': 'do Nascimento IJB, Abdulazeem HM, Vasanthan LT, et al. The global effect of digital health technologies on health workers’ competencies and health workplace: an umbrella review of systematic reviews and lexical-based and sentence-based meta-analysis. Lancet Digit Health. 2023 Aug;5(8):e534–e544. doi: 10.1016/S2589-7500(23)00092-4. doi. Medline.', 'ArticleIdList': [StringElement('10.1016/S2589-7500(23)00092-4', attributes={'IdType': 'doi'}), StringElement('PMC10397356', attributes={'IdType': 'pmc'}), StringElement('37507197', attributes={'IdType': 'pubmed'})]}, {'Citation': 'do Nascimento IJB, Abdulazeem H, Vasanthan LT, et al. Barriers and facilitators to utilizing digital health technologies by healthcare professionals. NPJ Digit Med. 2023 Sep 18;6(1):161. doi: 10.1038/s41746-023-00899-4. doi. Medline.', 'ArticleIdList': [StringElement('10.1038/s41746-023-00899-4', attributes={'IdType': 'doi'}), StringElement('PMC10507089', attributes={'IdType': 'pmc'}), StringElement('37723240', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Vuorikari R, Kluzer S, Punie Y. DigComp 22: The Digital Competence Framework for Citizens - With New Examples of Knowledge, Skills and Attitudes. Publications Office of the European Union; 2022. doi. ISBN.978-92-76-48883-5', 'ArticleIdList': [StringElement('10.2760/490274', attributes={'IdType': 'doi'})]}, {'Citation': 'Qué es la inteligencia artificial. Gobierno de España, Plan de Recuperación Transformación y Resiliencia.  [14-01-2025]. https://planderecuperacion.gob.es/noticias/que-es-inteligencia-artificial-ia-prtr URL. Accessed.'}, {'Citation': 'Russell S, Norvig P. Artificial Intelligence: A Modern Approach. 4th Global. Pearson – prentice hall; ISBN.0134610997'}, {'Citation': 'Mintz Y, Brodie R. Introduction to artificial intelligence in medicine. Minim Invasive Ther Allied Technol. 2019 Apr;28(2):73–81. doi: 10.1080/13645706.2019.1575882. doi. Medline.', 'ArticleIdList': [StringElement('10.1080/13645706.2019.1575882', attributes={'IdType': 'doi'}), StringElement('30810430', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Liu X, Zhang W, Zhang Q, et al. Development and validation of a machine learning-augmented algorithm for diabetes screening in community and primary care settings: a population-based study. Front Endocrinol (Lausanne) 2022;13:1043919. doi: 10.3389/fendo.2022.1043919. doi. Medline.', 'ArticleIdList': [StringElement('10.3389/fendo.2022.1043919', attributes={'IdType': 'doi'}), StringElement('PMC9742532', attributes={'IdType': 'pmc'}), StringElement('36518245', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Kim HS, Kim DJ, Yoon KH. Medical big data is not yet available: why we need realism rather than exaggeration. Endocrinol Metab (Seoul) 2019 Dec;34(4):349–354. doi: 10.3803/EnM.2019.34.4.349. doi. Medline.', 'ArticleIdList': [StringElement('10.3803/EnM.2019.34.4.349', attributes={'IdType': 'doi'}), StringElement('PMC6935779', attributes={'IdType': 'pmc'}), StringElement('31884734', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Arencibia MG, Cardero DM. Dilemas éticos en el escenario de la inteligencia artificial. Econom y Socied. 2020;25(57):1–18. doi: 10.15359/eys.25-57.5. doi.', 'ArticleIdList': [StringElement('10.15359/eys.25-57.5', attributes={'IdType': 'doi'})]}, {'Citation': 'Harvey HB, Gowda V. How the FDA regulates AI. Acad Radiol. 2020 Jan;27(1):58–61. doi: 10.1016/j.acra.2019.09.017. doi. Medline.', 'ArticleIdList': [StringElement('10.1016/j.acra.2019.09.017', attributes={'IdType': 'doi'}), StringElement('31818387', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Taloni A, Scorcia V, Giannaccare G. Large language model advanced data analysis abuse to create a fake data set in medical research. JAMA Ophthalmol. 2023 Dec 1;141(12):1174–1175. doi: 10.1001/jamaophthalmol.2023.5162. doi. Medline.', 'ArticleIdList': [StringElement('10.1001/jamaophthalmol.2023.5162', attributes={'IdType': 'doi'}), StringElement('PMC10636646', attributes={'IdType': 'pmc'}), StringElement('37943569', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Naddaf M. ChatGPT generates fake data set to support scientific hypothesis. Nature New Biol. 2023 Nov 30;623(7989):895–896. doi: 10.1038/d41586-023-03635-w. doi.', 'ArticleIdList': [StringElement('10.1038/d41586-023-03635-w', attributes={'IdType': 'doi'}), StringElement('37993616', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Lauricella LL, Pêgo-Fernandes PM. Databases, big data and artificial intelligence: what healthcare professionals need to know about them. Sao Paulo Med J. 2022;140(6):737–738. doi: 10.1590/1516-3180.2022.140611082022. doi.', 'ArticleIdList': [StringElement('10.1590/1516-3180.2022.140611082022', attributes={'IdType': 'doi'}), StringElement('PMC9671567', attributes={'IdType': 'pmc'}), StringElement('36169567', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Kamble SS, Gunasekaran A, Goswami M, Manda J. A systematic perspective on the applications of big data analytics in healthcare management. Int J Healthc Manag. 2019 Jul 3;12(3):226–240. doi: 10.1080/20479700.2018.1531606. doi.', 'ArticleIdList': [StringElement('10.1080/20479700.2018.1531606', attributes={'IdType': 'doi'})]}, {'Citation': 'Grunhut J, Wyatt AT, Marques O. Educating future physicians in artificial intelligence (AI): an integrative review and proposed changes. J Med Educ Curric Dev. 2021;8:23821205211036836. doi: 10.1177/23821205211036836. doi. Medline.', 'ArticleIdList': [StringElement('10.1177/23821205211036836', attributes={'IdType': 'doi'}), StringElement('PMC8580487', attributes={'IdType': 'pmc'}), StringElement('34778562', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Nagi F, Salih R, Alzubaidi M, et al. Applications of artificial intelligence (AI) in medical education: a scoping review. Stud Health Technol Inform. 2023 Jun 29;305:648–651. doi: 10.3233/SHTI230581. doi. Medline.', 'ArticleIdList': [StringElement('10.3233/SHTI230581', attributes={'IdType': 'doi'}), StringElement('37387115', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Stanfill MH, Marc DT. Health information management: implications of artificial intelligence on healthcare data and information management. Yearb Med Inform. 2019 Aug;28(1):56–64. doi: 10.1055/s-0039-1677913. doi. Medline.', 'ArticleIdList': [StringElement('10.1055/s-0039-1677913', attributes={'IdType': 'doi'}), StringElement('PMC6697524', attributes={'IdType': 'pmc'}), StringElement('31419816', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Charow R, Jeyakumar T, Younus S, et al. Artificial intelligence education programs for health care professionals: scoping review. JMIR Med Educ. 2021 Dec 13;7(4):e31043. doi: 10.2196/31043. doi. Medline.', 'ArticleIdList': [StringElement('10.2196/31043', attributes={'IdType': 'doi'}), StringElement('PMC8713099', attributes={'IdType': 'pmc'}), StringElement('34898458', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Moher D, Liberati A, Tetzlaff J, Altman DG, The PRISMA Group Preferred reporting items for systematic reviews and meta-analyses: the PRISMA statement. PLoS Med. 2009 Jul 21;6(7):e1000097. doi: 10.1371/journal.pmed.1000097. doi. Medline.', 'ArticleIdList': [StringElement('10.1371/journal.pmed.1000097', attributes={'IdType': 'doi'}), StringElement('PMC2707599', attributes={'IdType': 'pmc'}), StringElement('19621072', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Aguayo-Albasini JL, Flores-Pastor B, Soria-Aledo V. Sistema GRADE: clasificación de la calidad de la evidencia y graduación de la fuerza de la recomendación. Cir Esp. 2014 Feb;92(2):82–88. doi: 10.1016/j.ciresp.2013.08.002. doi.', 'ArticleIdList': [StringElement('10.1016/j.ciresp.2013.08.002', attributes={'IdType': 'doi'}), StringElement('24361098', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Hong QN, Fàbregues S, Bartlett G, et al. The Mixed Methods Appraisal Tool (MMAT) version 2018 for information professionals and researchers. Educ Inf. 2018 Dec 18;34(4):285–291. doi: 10.3233/EFI-180221. doi.', 'ArticleIdList': [StringElement('10.3233/EFI-180221', attributes={'IdType': 'doi'})]}, {'Citation': 'Higgins JPT, Thomas J, Chandler J, et al.   Cochrane Handbook for Systematic Reviews of Interventions Version 64. Cochrane; 2023.  [14-01-2025]. https://training.cochrane.org/handbook URL. Accessed.'}, {'Citation': 'Çalışkan SA, Demir K, Karaca O. Artificial intelligence in medical education curriculum: an e-Delphi study for competencies. PLoS ONE. 2022;17(7):e0271872. doi: 10.1371/journal.pone.0271872. doi. Medline.', 'ArticleIdList': [StringElement('10.1371/journal.pone.0271872', attributes={'IdType': 'doi'}), StringElement('PMC9302857', attributes={'IdType': 'pmc'}), StringElement('35862401', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Singh RP, Hom GL, Abramoff MD, Campbell JP, Chiang MF, AAO Task Force on Artificial Intelligence Current challenges and barriers to real-world artificial intelligence adoption for the healthcare system, provider, and the patient. Transl Vis Sci Technol. 2020 Aug;9(2):45. doi: 10.1167/tvst.9.2.45. doi. Medline.', 'ArticleIdList': [StringElement('10.1167/tvst.9.2.45', attributes={'IdType': 'doi'}), StringElement('PMC7443115', attributes={'IdType': 'pmc'}), StringElement('32879755', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Liaw W, Kueper JK, Lin S, Bazemore A, Kakadiaris I. Competencies for the use of artificial intelligence in primary care. Ann Fam Med. 2022;20(6):559–563. doi: 10.1370/afm.2887. doi. Medline.', 'ArticleIdList': [StringElement('10.1370/afm.2887', attributes={'IdType': 'doi'}), StringElement('PMC9705044', attributes={'IdType': 'pmc'}), StringElement('36443071', attributes={'IdType': 'pubmed'})]}, {'Citation': 'McCoy LG, Nagaraj S, Morgado F, Harish V, Das S, Celi LA. What do medical students actually need to know about artificial intelligence? NPJ Digit Med. 2020;3(1):86. doi: 10.1038/s41746-020-0294-7. doi. Medline.', 'ArticleIdList': [StringElement('10.1038/s41746-020-0294-7', attributes={'IdType': 'doi'}), StringElement('PMC7305136', attributes={'IdType': 'pmc'}), StringElement('32577533', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Sujan MA, White S, Habli I, Reynolds N. Stakeholder perceptions of the safety and assurance of artificial intelligence in healthcare. Saf Sci. 2022 Nov;155(8):105870. doi: 10.1016/j.ssci.2022.105870. doi.', 'ArticleIdList': [StringElement('10.1016/j.ssci.2022.105870', attributes={'IdType': 'doi'})]}, {'Citation': 'Wiljer D, Hakim Z. Developing an artificial intelligence-enabled health care practice: rewiring health care professions for better care. J Med Imaging Radiat Sci. 2019 Dec;50(4 Suppl 2):S8–S14. doi: 10.1016/j.jmir.2019.09.010. doi. Medline.', 'ArticleIdList': [StringElement('10.1016/j.jmir.2019.09.010', attributes={'IdType': 'doi'}), StringElement('31791914', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Sapci AH, Sapci HA. Artificial intelligence education and tools for medical and health informatics students: systematic review. JMIR Med Educ. 2020 Jun 30;6(1):e19285. doi: 10.2196/19285. doi. Medline.', 'ArticleIdList': [StringElement('10.2196/19285', attributes={'IdType': 'doi'}), StringElement('PMC7367541', attributes={'IdType': 'pmc'}), StringElement('32602844', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Garvey KV, Craig KJT, Russell R, Novak LL, Moore D, Miller BM. Considering clinician competencies for the implementation of artificial intelligence-based tools in health care: findings from a scoping review. JMIR Med Inform. 2022 Nov 16;10(11):e37478. doi: 10.2196/37478. doi. Medline.', 'ArticleIdList': [StringElement('10.2196/37478', attributes={'IdType': 'doi'}), StringElement('PMC9713618', attributes={'IdType': 'pmc'}), StringElement('36318697', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Abuzaid MM, Elshami W, Fadden SM. Integration of artificial intelligence into nursing practice. Health Technol (Berl) 2022;12(6):1109–1115. doi: 10.1007/s12553-022-00697-0. doi. Medline.', 'ArticleIdList': [StringElement('10.1007/s12553-022-00697-0', attributes={'IdType': 'doi'}), StringElement('PMC9470236', attributes={'IdType': 'pmc'}), StringElement('36117522', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Faes L, Liu X, Wagner SK, et al. A clinician’s guide to artificial intelligence: how to critically appraise machine learning studies. Transl Vis Sci Technol. 2020 Feb 12;9(2):7. doi: 10.1167/tvst.9.2.7. doi. Medline.', 'ArticleIdList': [StringElement('10.1167/tvst.9.2.7', attributes={'IdType': 'doi'}), StringElement('PMC7346877', attributes={'IdType': 'pmc'}), StringElement('32704413', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Nagy M, Radakovich N, Nazha A. Why machine learning should be taught in medical schools. Med Sci Educ. 2022 Apr;32(2):529–532. doi: 10.1007/s40670-022-01502-3. doi. Medline.', 'ArticleIdList': [StringElement('10.1007/s40670-022-01502-3', attributes={'IdType': 'doi'}), StringElement('PMC9054965', attributes={'IdType': 'pmc'}), StringElement('35528308', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Stöger K, Schneeberger D, Kieseberg P, Holzinger A. Legal aspects of data cleansing in medical AI. Comput Law Secur Rev. 2021 Sep;42:105587. doi: 10.1016/j.clsr.2021.105587. doi.', 'ArticleIdList': [StringElement('10.1016/j.clsr.2021.105587', attributes={'IdType': 'doi'})]}, {'Citation': 'European Commission  Official Journal of the European Union; Regulation (EU) 2023/206 on artificial intelligence. EU Artificial Intelligence Act. 2024.  [14-01-2025]. https://artificialintelligenceact.eu/the-act/ URL. Accessed.'}, {'Citation': 'Lysaght T, Lim HY, Xafis V, Ngiam KY. AI-assisted decision-making in healthcare. ABR. 2019 Sep;11(3):299–314. doi: 10.1007/s41649-019-00096-0. doi.', 'ArticleIdList': [StringElement('10.1007/s41649-019-00096-0', attributes={'IdType': 'doi'}), StringElement('PMC7747260', attributes={'IdType': 'pmc'}), StringElement('33717318', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Savage N. Breaking into the black box of artificial intelligence. Nature New Biol. 2022 Mar 29; doi: 10.1038/d41586-022-00858-1. doi. Medline.', 'ArticleIdList': [StringElement('10.1038/d41586-022-00858-1', attributes={'IdType': 'doi'}), StringElement('35352042', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Milam ME, Koo CW. The current status and future of FDA-approved artificial intelligence tools in chest radiology in the United States. Clin Radiol. 2023 Feb;78(2):115–122. doi: 10.1016/j.crad.2022.08.135. doi. Medline.', 'ArticleIdList': [StringElement('10.1016/j.crad.2022.08.135', attributes={'IdType': 'doi'}), StringElement('36180271', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Khanra S, Dhir A, Islam A, Mäntymäki M. Big data analytics in healthcare: a systematic literature review. Ent Inf Syst. 2020 Aug 8;14(7):878–912. doi: 10.1080/17517575.2020.1812005. doi.', 'ArticleIdList': [StringElement('10.1080/17517575.2020.1812005', attributes={'IdType': 'doi'})]}, {'Citation': 'James CA, Wheelock KM, Woolliscroft JO. Machine learning: the next paradigm shift in medical education. Acad Med. 2021 Jul 1;96(7):954–957. doi: 10.1097/ACM.0000000000003943. doi. Medline.', 'ArticleIdList': [StringElement('10.1097/ACM.0000000000003943', attributes={'IdType': 'doi'}), StringElement('33496428', attributes={'IdType': 'pubmed'})]}, {'Citation': 'AAMC  . Arizona Telemedine Program. AAMC; 2021.  [14-01-2025]. AAMC new and emerging areas in medicine series; telehealth competencies across the learning continuum.https://telemedicine.arizona.edu/sites/default/files/training/2022/Feb/5%20-%20AAMC-2021-telehealth-competencies%20across%20the%20learning%20continum.pdf URL. Accessed.'}, {'Citation': 'Zweig M, Desiliva J. Q1 2021 funding report: digital health is all grown up. Rock Health. 2021.  [14-01-2025]. https://rockhealth.com/insights/q1-2021-funding-report-digital-health-is-all-grown-up/ URL. Accessed.'}, {'Citation': 'Marwaha JS, Landman AB, Brat GA, Dunn T, Gordon WJ. Deploying digital health tools within large, complex health systems: key considerations for adoption and implementation. NPJ Digit Med. 2022 Jan 27;5(1):13. doi: 10.1038/s41746-022-00557-1. doi. Medline.', 'ArticleIdList': [StringElement('10.1038/s41746-022-00557-1', attributes={'IdType': 'doi'}), StringElement('PMC8795422', attributes={'IdType': 'pmc'}), StringElement('35087160', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Chan KS, Zary N. Applications and challenges of implementing artificial intelligence in medical education: integrative review. JMIR Med Educ. 2019 Jun 15;5(1):e13930. doi: 10.2196/13930. doi. Medline.', 'ArticleIdList': [StringElement('10.2196/13930', attributes={'IdType': 'doi'}), StringElement('PMC6598417', attributes={'IdType': 'pmc'}), StringElement('31199295', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Grunhut J, Marques O, Wyatt ATM. Needs, challenges, and applications of artificial intelligence in medical education curriculum. JMIR Med Educ. 2022 Jun 7;8(2):e35587. doi: 10.2196/35587. doi. Medline.', 'ArticleIdList': [StringElement('10.2196/35587', attributes={'IdType': 'doi'}), StringElement('PMC9214616', attributes={'IdType': 'pmc'}), StringElement('35671077', attributes={'IdType': 'pubmed'})]}, {'Citation': 'Stanford center for professional development. Stanford University.  [14-01-2025]. https://online.stanford.edu/ URL. Accessed.'}, {'Citation': 'Artificial intelligence in medicine program. Harvard University.  [14-01-2025]. https://aim.hms.harvard.edu/ URL. Accessed.'}, {'Citation': 'Heckman GA, Hirdes JP, McKelvie RS. The role of physicians in the era of big data. Can J Cardiol. 2020 Jan;36(1):19–21. doi: 10.1016/j.cjca.2019.09.018. doi. Medline.', 'ArticleIdList': [StringElement('10.1016/j.cjca.2019.09.018', attributes={'IdType': 'doi'}), StringElement('31787436', attributes={'IdType': 'pubmed'})]}]}], 'History': [DictElement({'Year': '2024', 'Month': '3', 'Day': '7'}, attributes={'PubStatus': 'received'}), DictElement({'Year': '2024', 'Month': '10', 'Day': '4'}, attributes={'PubStatus': 'revised'}), DictElement({'Year': '2025', 'Month': '1', 'Day': '2'}, attributes={'PubStatus': 'accepted'}), DictElement({'Year': '2025', 'Month': '2', 'Day': '6', 'Hour': '6', 'Minute': '21'}, attributes={'PubStatus': 'medline'}), DictElement({'Year': '2025', 'Month': '2', 'Day': '6', 'Hour': '6', 'Minute': '20'}, attributes={'PubStatus': 'pubmed'}), DictElement({'Year': '2025', 'Month': '2', 'Day': '6', 'Hour': '5', 'Minute': '3'}, attributes={'PubStatus': 'entrez'}), DictElement({'Year': '2025', 'Month': '2', 'Day': '5'}, attributes={'PubStatus': 'pmc-release'})], 'PublicationStatus': 'epublish', 'ArticleIdList': [StringElement('39912237', attributes={'IdType': 'pubmed'}), StringElement('PMC11822726', attributes={'IdType': 'pmc'}), StringElement('10.2196/58161', attributes={'IdType': 'doi'}), StringElement('v11i1e58161', attributes={'IdType': 'pii'})]}}]}


def parse_pubmed_systematic_review_data(  # noqa: C901, PLR0912, PLR0915
    entrez_record: dict[str, t.Any],
) -> dict[str, t.Any]:
    """Parse a PubmedArticle record from an Entrez response.

    Parse a PubmedArticle record from an Entrez response (as a Python dict)
    and extract metadata relevant for systematic reviews.

    This version additionally:
      - Extracts DOI and PMCID from the ArticleIdList in PubMedData
      - Attempts to extract IDs from the references
      - Recursively cleans the final output to remove custom Entrez objects
    """
    # Get the list of articles (usually under "PubmedArticle")
    pubmed_articles = entrez_record.get("PubmedArticle", [])
    if not pubmed_articles:
        return {}

    # Process the first article
    article_entry = pubmed_articles[0]
    medline_citation = article_entry.get("MedlineCitation", {})
    pubmed_data = article_entry.get("PubmedData", {})

    # ---- PMID and Dates ----
    pmid = extract_text(medline_citation.get("PMID", ""))
    date_completed = medline_citation.get(
        "DateCompleted", {}
    )  # e.g., {"Year": "2025", ...}
    date_revised = medline_citation.get("DateRevised", {})

    # ---- Article Information ----
    article = medline_citation.get("Article", {})
    article_title = extract_text(article.get("ArticleTitle", ""))

    # Process the abstract (may have multiple segments)
    abstract_dict = article.get("Abstract", {})
    abstract_text_list = [
        extract_text(abs_item) for abs_item in abstract_dict.get("AbstractText", [])
    ]
    abstract_text = "\n\n".join(abstract_text_list)

    # ---- Journal Info ----
    journal_info = article.get("Journal", {})
    journal_title = extract_text(journal_info.get("Title", ""))
    journal_issue = journal_info.get("JournalIssue", {})
    pub_date = journal_issue.get("PubDate", {})
    journal_pub_year = extract_text(pub_date.get("Year", ""))
    journal_pub_month = extract_text(pub_date.get("Month", ""))
    journal_pub_day = extract_text(pub_date.get("Day", ""))
    volume = extract_text(journal_issue.get("Volume", ""))

    # ---- IDs: DOI, PMCID (and optionally override PMID) ----
    # First, check ArticleIdList in PubmedData.
    doi = None
    pmcid = None
    article_ids = pubmed_data.get("ArticleIdList", [])
    for aid in article_ids:
        if hasattr(aid, "attributes"):
            id_type = aid.attributes.get("IdType")
            if id_type == "doi":
                doi = extract_text(aid)
            elif id_type == "pmc":
                pmcid = extract_text(aid)
            # Optionally, update pmid from here if needed.
    # Fallback: if DOI not found, try ELocationID in the Article.
    if not doi:
        for loc_item in article.get("ELocationID", []):
            if (
                hasattr(loc_item, "attributes")
                and loc_item.attributes.get("EIdType") == "doi"
            ):
                doi = extract_text(loc_item)
                break

    # ---- Authors ----
    raw_authors = article.get("AuthorList", [])
    # Sometimes AuthorList may be a dict containing "Author"
    if isinstance(raw_authors, dict):
        raw_authors = raw_authors.get("Author", [])

    author_list = (
        [
            {
                "last_name": extract_text(author_item.get("LastName", "")),
                "fore_name": extract_text(author_item.get("ForeName", "")),
                "initials": extract_text(author_item.get("Initials", "")),
                "affiliations": [
                    extract_text(aff_item.get("Affiliation", ""))
                    for aff_item in author_item.get("AffiliationInfo", [])
                ],
            }
            for author_item in raw_authors
        ]
        if isinstance(raw_authors, list)
        else []
    )

    # ---- Publication Types ----
    publication_types = [
        extract_text(pt) for pt in article.get("PublicationTypeList", [])
    ]

    # ---- Keywords ----
    keywords = []
    keyword_lists = medline_citation.get("KeywordList", [])
    for kw_list in keyword_lists:
        if isinstance(kw_list, list):
            keywords.extend(extract_text(kw) for kw in kw_list)
        else:
            keywords.append(extract_text(kw_list))

    # ---- MeSH Headings ----
    mesh_headings_list = medline_citation.get("MeshHeadingList", [])
    mesh_headings = []
    for mh_item in mesh_headings_list:
        descriptor = mh_item.get("DescriptorName", {})
        mesh_headings.append(extract_text(descriptor))

    # ---- Conflict of Interest (COI) ----
    coi_statement = extract_text(medline_citation.get("CoiStatement", ""))

    # ---- References ----
    references = []
    reference_lists = pubmed_data.get("ReferenceList", [])
    for ref_block in reference_lists:
        for ref_item in ref_block.get("Reference", []):
            citation_text = extract_text(ref_item.get("Citation", ""))
            r_doi, r_pmid, r_pmc = None, None, None
            article_ids = ref_item.get("ArticleIdList", [])
            for a_id in article_ids:
                if hasattr(a_id, "attributes"):
                    id_type = a_id.attributes.get("IdType")
                    val = extract_text(a_id)
                    if id_type == "pubmed":
                        r_pmid = val
                    elif id_type == "pmc":
                        r_pmc = val
                    elif id_type == "doi":
                        r_doi = val
            references.append(
                {
                    "citation": citation_text,
                    "pmid": r_pmid,
                    "pmc": r_pmc,
                    "doi": r_doi,
                }
            )

    result = {
        "pmid": pmid,
        "date_completed": date_completed,
        "date_revised": date_revised,
        "article_title": article_title,
        "abstract": abstract_text,
        "journal_title": journal_title,
        "journal_volume": volume,
        "journal_pub_date": {
            "year": journal_pub_year,
            "month": journal_pub_month,
            "day": journal_pub_day,
        },
        "doi": doi,
        "pmcid": pmcid,
        "authors": author_list,
        "publication_types": publication_types,
        "keywords": keywords,
        "mesh_headings": mesh_headings,
        "coi_statement": coi_statement,
        "references": references,
        "publication_status": extract_text(pubmed_data.get("PublicationStatus", "")),
        "history": pubmed_data.get("History", []),
    }

    # Clean the result recursively to remove any leftover custom objects.
    return recursive_clean(result)  # pyright: ignore [reportReturnType]


# Example usage:
# parsed_result = parse_pubmed_systematic_review_data(records)
# print(parsed_result)
