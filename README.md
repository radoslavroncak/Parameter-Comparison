# Parameter-Comparison
Porovnavanie parametrov IDX vs ICC-print

## Pouzitie

Program porovna parametre z dvoch `.txt` suborov:

```bash
python3 compare_parameters.py prvy_subor.txt druhy_subor.txt
```

Ocakavany format riadku je napr.:
- `nazov=hodnota`
- `nazov: hodnota`
- `nazov hodnota`

Program vypise:
- parametre iba v prvom subore
- parametre iba v druhom subore
- parametre s rozdielnou hodnotou
