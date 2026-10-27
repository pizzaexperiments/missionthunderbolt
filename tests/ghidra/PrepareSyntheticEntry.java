// Set a known entrypoint in a tiny newly authored synthetic 68000 fixture.
import ghidra.app.script.GhidraScript;
public class PrepareSyntheticEntry extends GhidraScript {
    @Override public void run() throws Exception {
        if(!currentProgram.getName().equals("CODE_99_000.bin") && !currentProgram.getName().equals("CODE_98_000.bin"))
            throw new IllegalArgumentException("Synthetic test fixture only");
        if(!disassemble(toAddr(0)))throw new IllegalStateException("Synthetic entry did not disassemble");
        if(getFunctionAt(toAddr(0))==null)createFunction(toAddr(0),"synthetic_entry");
    }
}
