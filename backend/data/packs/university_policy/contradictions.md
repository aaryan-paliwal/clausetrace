# ClauseTrace — Planted Contradictions & Test Boundary Reference

**Document Version:** 1.0  
**Purpose:** Ground-truth reference for evaluation, pipeline benchmarking, and contradiction classification audit.  
**Corpus:** Western Oak University Policy Documents (6 documents, 6,806 total words)

---

## 1. Overview of Planted Inconsistencies

To rigorously benchmark ClauseTrace's three-way contradiction classification pipeline (`GENUINE_CONTRADICTION`, `EXCEPTION`, `COMPLEMENTARY`), three real cross-document contradictions were deliberately planted across the institutional documents.

These contradictions:
1. Occur across distinct documents.
2. Address the identical subject, scope, and situation.
3. State mutually incompatible rules or numeric thresholds.
4. Do NOT use exception or qualifier phrasing (such as *"unless"*, *"for students in..."*, *"except"*, *"special case"*, or *"supersedes"*).

---

## 2. Planted Cross-Document Contradictions (Ground Truth)

### Contradiction 1: Maximum Undergraduate Credit Load

- **Contradiction ID:** `CONT-01`
- **Topic:** Maximum normal undergraduate semester credit load
- **Document A:** `corpus/documents/academic_policy.md`
  - **Section:** Section 2.2 (*Normal Semester Credit Loads*)
  - **Exact Conflicting Rule:**  
    > "The maximum normal credit load permissible for any undergraduate student during an Autumn or Spring term is 18 credits. Any course enrollment exceeding this ceiling requires formal approval via an Academic Overload Petition submitted to the Department Chair and Dean of Faculty."
- **Document B:** `corpus/documents/registration_guide.pdf`
  - **Section:** Section 2.1 (*Standard Credit Allowances and Term Capacities*, Page 2)
  - **Exact Conflicting Rule:**  
    > "The maximum credit load for undergraduate students during a regular semester is 21 credits. The automated registration software permits students in good academic standing to add coursework up to this 21-credit ceiling directly through the online self-service interface without requiring individual administrative approval or departmental advisor overrides."
- **Why Incompatible:**  
  Both rules govern the same general undergraduate population during regular Autumn/Spring terms. One explicitly caps normal un-petitioned registration at 18 credits (requiring formal overload petitions for 19+ credits), while the other establishes an un-petitioned automated maximum credit load of 21 credits (requiring overload petitions only at 22+ credits). They cannot both be true simultaneously.
- **Expected ClauseTrace Classification:** `CONTRADICTION` (`GENUINE_CONTRADICTION`)

---

### Contradiction 2: Absolute Grade Appeal Filing Deadline

- **Contradiction ID:** `CONT-02`
- **Topic:** Absolute deadline to file a formal grade appeal
- **Document A:** `corpus/documents/academic_policy.md`
  - **Section:** Section 5.2 (*Mandatory Resolution Timelines and Protocol*, Step 2)
  - **Exact Conflicting Rule:**  
    > "The absolute deadline to lodge a formal grade appeal is exactly 30 calendar days following the official posting of the final semester grade report by the University Registrar. Appeals received after the expiration of 30 calendar days will be summarily dismissed without administrative review."
- **Document B:** `corpus/documents/student_conduct.md`
  - **Section:** Article VI, Section 6.2 (*Grade Appeals Adjudication Deadline*)
  - **Exact Conflicting Rule:**  
    > "To ensure complete fairness, evidentiary compilation, and adequate departmental review, the absolute deadline to lodge a formal grade appeal is exactly 45 business days following the official posting of final semester grades."
- **Why Incompatible:**  
  Both policies dictate the deadline for submitting a formal grade appeal for an assigned course grade following the publication of semester marks. Document A imposes a 30 calendar day cutoff; Document B establishes a 45 business day cutoff (which spans over 9 calendar weeks). An appeal submitted on day 35 calendar days would be summarily dismissed under Document A but fully compliant and timely under Document B.
- **Expected ClauseTrace Classification:** `CONTRADICTION` (`GENUINE_CONTRADICTION`)

---

### Contradiction 3: Week-4 Course Withdrawal Tuition Refund Percentage

- **Contradiction ID:** `CONT-03`
- **Topic:** Tuition refund percentage for term withdrawal during Week 4
- **Document A:** `corpus/documents/fee_schedule.md`
  - **Section:** Section 5.1 & 5.2 (*Official Institutional Tuition Refund Table & Policy on Week-4 Term Withdrawals*)
  - **Exact Conflicting Rule:**  
    > "As codified in Table 5.1 above, any student who officially withdraws from a course or from the university during the fourth week of the semester (instructional calendar days 22 through 28) is entitled to an institutional tuition refund of exactly 50%."
- **Document B:** `corpus/documents/financial_aid.md`
  - **Section:** Section 5.2 & 5.3 (*Mandatory Withdrawal Refund Schedule for Financial Aid Recipients & Specific Policy on Week-4 Term Withdrawals*)
  - **Exact Conflicting Rule:**  
    > "As established in Section 5.2 and the refund schedule above, any student who officially withdraws from a course or from the university during the fourth week of the semester (instructional days 22 through 28) is entitled to an institutional tuition refund of exactly 25%."
- **Why Incompatible:**  
  Both policies stipulate the exact financial refund percentage granted to a matriculated student withdrawing during the fourth week (instructional days 22 through 28). One policy guarantees a 50% refund, while the other decrees a 25% refund. A student cannot receive both 50% and 25% refund for the identical withdrawal event.
- **Expected ClauseTrace Classification:** `CONTRADICTION` (`GENUINE_CONTRADICTION`)

---

## 3. Legitimate Exception Contrast (Negative Control for Contradiction Classifier)

To verify that ClauseTrace does not falsely classify legitimate exceptions as contradictions:

### Legitimate Exception Case: Physical Classroom Attendance Threshold
- **General Rule:** `corpus/documents/academic_policy.md` (Section 4.1)
  - Rule: Undergraduate and graduate students must maintain a minimum physical classroom attendance rate of 75%.
- **Legitimate Exception:** `corpus/documents/academic_policy.md` (Section 4.2)
  - Rule: Students with documented severe medical convalescence validated by Student Health Services receive an authorized reduction in attendance threshold to 60%.
- **Why This is NOT a Contradiction:**  
  The 60% threshold explicitly conditions on an administrative medical accommodation protocol ("Approved Medical Exemption Provision"), acting as an authorized subordinate exception rather than an incompatible conflict.
- **Expected ClauseTrace Classification:** `EXCEPTION` (or `ANSWERABLE` with conditional answer explaining the general rule + medical exception).
