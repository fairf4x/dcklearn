To simply generate resulting FSA image run:
simple test:
```python learnFSA.py -p PLANDIR -o OUTNAME -f png```

Image output formats available (through ```graphviz.Digraph.render```): ```png```,```pdf```,```svg```
It is also possible to save FSA as a graph in ```gv``` format using ```graphviz.Digraph.save```.
In that case set ```-f``` to ```gv```.

In order to test merging FSA into PDDL domain. THIS DOES NOT WORK.
test merge2PDDL:
```python learnFSA.py -p PLANDIR -r ".*" -m DOMAIN.pddl```


