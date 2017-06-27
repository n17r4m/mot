
var util_path = "/home/cmput/project/util/"
var fs = Npm.require('fs')

export function pyConfig(name){
    var data = fs.readFileSync(util_path + name + ".json", 'utf8')
    return JSON.parse(data)
}