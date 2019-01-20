; Print "Hello World!" 5 times
; Use Loops to achieve the aforementioned output

; Execution Phase
.ORIG x3000

LEA R0, HELLO   ; R0 = "Hello....!"
LD R1, COUNTER  ; R1 = 5

LOOP TRAP x22   ; Print Hello World
ADD R1, R1, #-1 ; Decrement Counter
BRp LOOP    ; Returns to LOOP label until Counter is 0 (nonpositive)

HALT

; Non-Exec. phase

HELLO .STRINGZ "Hello, World!\n" ; \n = new line
COUNTER .fill #5        ; Counter = 5

.END    ; End Program
