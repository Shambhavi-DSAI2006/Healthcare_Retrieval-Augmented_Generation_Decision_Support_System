##### 

### Output Tables of queries.sql

##### 

##### 

##### AGGREGATION QUERIES



Query 1: Count number of chunks in each section



section\_id	total\_chunks

1		1180





Query 2: Average factuality and consistency scores



avg\_factuality	         avg\_consistency

0.891285714149475	0.860285714932851





Query 3: Total number of user queries



total\_queries

70



Query 4: Average confidence score of generated responses



average\_confidence

0.896857142754964





##### JOIN QUERIES



Query 5: Show responses with their factuality and consistency scores



response\_id	generated\_answer						factuality\_score	consistency\_score

1		WHO states dengue symptoms include fever, headache, and nausea.	0.970000028610229	0.939999997615814

2		COVID-19 vaccines significantly reduce severe illness risk.	0.949999988079071	0.920000016689301

3		Diabetes management includes monitoring blood sugar levels.	0.930000007152557	0.910000026226044

4		Malaria is transmitted through infected mosquito bites.		0.959999978542328	0.930000007152557

5		Common vaccine side effects include fever and fatigue.		0.899999976158142	0.879999995231628



(Showing only top 5 rows in this text file)







Query 6: Show chunk text with associated topic names







chunk\_id	chunk\_text								topic\_name

1		Dengue symptoms include fever, headache, nausea, and muscle pain.	Dengue

2		Severe dengue may cause internal bleeding and shock.			COVID-19

3		Mosquito control helps prevent dengue transmission.			Vaccination

4		COVID-19 vaccines reduce severe illness and hospitalization.		Diabetes

5		Vaccination programs improve public health outcomes.			Hypertension

6		Common vaccine side effects include fatigue and fever.			Malaria

7		Diabetes management requires monitoring blood glucose levels.		Asthma

8		Healthy diet and regular exercise are important for treatment.		Stroke

9		Insulin therapy may be necessary for some patients.			Nutrition

10		Malaria spreads through infected mosquito bites.			Public Health







##### SUBQUERY ANALYSIS



Query 7: Find responses with confidence score higher than average



response\_id	generated\_answer								confidence\_score

1		WHO states dengue symptoms include fever, headache, and nausea.			0.949999988079071

2		COVID-19 vaccines significantly reduce severe illness risk.			0.930000007152557

3		Diabetes management includes monitoring blood sugar levels.			0.910000026226044

4		Malaria is transmitted through infected mosquito bites.				0.939999997615814

6		Asthma symptoms include wheezing, coughing, and breathing difficulty.		0.930000007152557



(Showing only top 5 rows in this text file)









Query 8: Find chunks that have above-average relevance scores



query\_id	chunk\_id	relevance\_score

1			1	0.959999978542328

2			4	0.949999988079071

5			5	0.939999997615814

3			6	0.930000007152557

4			8	0.970000028610229

6			20	0.939999997615814

7			21	0.959999978542328

10			24	0.970000028610229

13			27	0.949999988079071

15			29	0.930000007152557



##### 

##### COMMON TABLE EXPRESSIONS (CTEs)



Query 9: Average chunk relevance per query using CTE



query\_id	avg\_relevance

10		0.970000028610229

7		0.959999978542328

13		0.949999988079071

5		0.939999997615814

6		0.939999997615814

1		0.939999997615814

4		0.935000002384186

3		0.930000007152557

15		0.930000007152557

8		0.920000016689301

2		0.919999986886978

9		0.910000026226044

12		0.899999976158142

11		0.889999985694885

14		0.879999995231628





Query 10: Count chunks per topic using CTE



topic\_name	total\_chunks

Asthma		1

COVID-19	1

Dengue		1

Diabetes	1

Hypertension	1

Malaria		1

Nutrition	1

Public Health	1

Stroke		1

Vaccination	1



##### WINDOW FUNCTION ANALYSIS



Query 11: Rank responses by confidence score



response\_id	confidence\_score	confidence\_rank

46			0.98			1

63			0.97			2

25			0.97			2

39			0.96			4

67			0.96			4

(Showing only top 5 rows in this text file)





Query 12: Rank chunks by relevance score within each query



query\_id	    chunk\_id	relevance\_score		relevance\_rank

1			1	0.959999978542328		1

1			2	0.920000016689301		2

2			4	0.949999988079071		1

2			10	0.889999985694885		2

3			6	0.930000007152557		1

4			8	0.970000028610229		1

4			9	0.899999976158142		2

5			5	0.939999997615814		1

6			20	0.939999997615814		1

7			21	0.959999978542328		1

8			22	0.920000016689301		1

9			23	0.910000026226044		1

10			24	0.970000028610229		1

11			25	0.889999985694885		1

12			26	0.899999976158142		1

13			27	0.949999988079071		1

14			28	0.879999995231628		1

15			29	0.930000007152557		1

