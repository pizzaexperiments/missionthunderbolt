// Record raw segment imports without emitting proprietary bytes or guessed symbols.
// @category MissionThunderbolt
import ghidra.app.script.GhidraScript;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

public class RecordImport extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected private metadata output directory");
        Path output = Path.of(args[0]);
        Files.createDirectories(output);
        String report = String.format(Locale.ROOT,
            "{\"program\":\"%s\",\"language\":\"%s\",\"base\":\"%s\",\"bytes\":%d,\"sha256\":\"%s\",\"analyzed\":false,\"runtime_address_known\":false}%n",
            currentProgram.getName(), currentProgram.getLanguageID(), currentProgram.getImageBase(),
            currentProgram.getMemory().getSize(), currentProgram.getExecutableSHA256());
        Files.writeString(output.resolve(currentProgram.getName() + ".json"), report);
        println("Recorded import metadata for " + currentProgram.getName());
    }
}
