# HP Programs

A selection of HP programs.

Capitalized filenames indicate the file is an HP48 binary object. A `.txt`extension indicates the file is a UserRPL program. An `.asc` extension indicates that file contains a program that was encoded by `->ASC` and must be decoded (by  `ASC->`) before use.

Name | Desc | Size (bytes)
----------|--------|--------:
[zips] | Directory containing original packages of some programs below | 0
[asc.txt](https://www.hpcalc.org/hp48/docs/faq/48faq-9.html#ss9.1) | A Uuencode-like program. When `SETUP` is run on the HP48G, it will create the `ASC->` and `->ASC` programs. `ASC->` may then be used to decode other programs. | 2,246
ascmit.txt | Encodes a program to an ASCII string and transmits the string over the serial port. The program relies on the `->ASC` program, so it must be available. | 594
CST.COMMA.txt | A trimmed-down version of CST.NUMFMT containing only the COMMA menu item. | 1,565
[CST.NUMFMT](https://www.hpcalc.org/details/2844) | A CST menu which can format the top object on the stack to make it more readable. e.g. `1000000000` will be formatted as `1,000,000,000`. CST.NUMFMT can format integers, degrees/minutes/seconds, currency, and more. Does not seem to work with any stack-replacement programs. | 4,130
[FACTOR13](https://www.hpcalc.org/details/1244) | A small UserRPN program which factors numbers.  | 113
[fixit.asc](https://www.hpcalc.org/hp48/docs/faq/48faq-9.html#ss9.3) | Correct the issue when an incorrectly downloaded program leaves a string beginning with 'HPHP48...' on the stack. This was written by HP. See also: OBJFIX and SPTR | 1,622
[FXRECV](https://www.hpcalc.org/hp48/docs/faq/48faq-6.html#ss6.14) | Bugfix for the HP48G's XRECV instruction. Pre-Rev R. G Series 48's had a bug that would sometimes cause XRECV to fail if there was not twice the amount of room free for the incoming file. | 99
[KIWIDEMO](https://www.hpcalc.org/details/1078) | Runs a two-minute demo of various graphic animations. Written by "The Kiwi Team". Author info is also displayed during the demo. The demo can be interrupted by pressing `[ON]` and `[C]` at the same time. | 12,317
[objfix.asc](https://www.hpcalc.org/hp48/docs/faq/48faq-9.html#ss9.2) | Similar to FIXIT and SPTR | 721
[PAS48](https://www.hpcalc.org/details/6268) | Generates a Sierpinski triangle. | 56
[SOLTAIR](https://www.hpcalc.org/details/4293) | A peg-jump solitaire game on a cross-shaped board. | 1,979
[sptr.txt](https://www.hpcalc.org/hp48/docs/faq/48faq-6.html#ss6.11) | A short UserRPL program which performs a similar function as OBJFIX and FIXIT. | 446
[STK5](https://www.hpcalc.org/details/2666) | A 5 or 7 line stack replacement program. When entering new values, the stack is pushed up which completely hides all of `5:` and the top two pixel rows of `4:`. Set flag 30 to exit program (`30` `[MODES]` `\|FLAGS\|` `\|SF\|`). Does not work with NUMFMT. | 504
[STKD.LIB](https://www.hpcalc.org/details/2665) | A 5 or 7 line stack replacement library. When entering new values, the stack does not move. The input line completely obscures all of `1:` and the bottom pixel row of `2:`. Program can exited via the LIBRARY menu. Does not work with NUMFMT. | 1,044

[hpcalc.org](https://www.hpcalc.org/) is an excellent source for more programs and other info.
