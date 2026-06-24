# Parameter-Comparison
Porovnavanie parametrov IDX vs ICC-print.

## Pouzitie

```bash
python3 compare_parameters.py <subor1.txt> <subor2.txt>
```

Volitelne je mozne vytvorit podsubory podla typu blokov (`TYPE`):

```bash
python3 compare_parameters.py <subor1.txt> <subor2.txt> --split-output-dir ./output
```

Program podporuje oba vstupne formaty:
- blokovy format `NAME/TYPE/.../END`
- plochy format `BLOK.PARAMETER = hodnota` (napr. exporty v UTF-16)
